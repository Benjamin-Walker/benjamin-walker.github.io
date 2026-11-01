"""Source-preservation tests: python3 -m unittest discover -s scripts."""

from pathlib import Path
import unittest

from local_preview import HTMLFields, content_fields, patch_source, revision, validate_inline


ROOT = Path(__file__).resolve().parent.parent


class LocalEditorTests(unittest.TestCase):
    def test_html_patch_preserves_links_scripts_and_surrounding_source(self):
        source = '<html><body><p>\n  Old <a href="https://example.com/">link</a>.\n</p><script>const example = "<p>not a field</p>";</script></body></html>'
        fields = HTMLFields(source).fields
        self.assertEqual(len(fields), 1)
        updated = patch_source(source, fields, [{"id": "html-0", "value": 'New <a href="https://example.com/">link</a> &amp; more.'}])
        self.assertEqual(updated, source.replace('Old <a href="https://example.com/">link</a>.', 'New <a href="https://example.com/">link</a> &amp; more.'))

    def test_data_patch_preserves_all_other_values_and_exports(self):
        source = (ROOT / "content.js").read_text()
        data, fields = content_fields(source)
        text = 'A title with "quotes", an apostrophe\'s, £ and a newline\nnext line'
        updated = patch_source(source, fields, [{"id": "personal.title", "value": text}], content=True)
        new_data, _ = content_fields(updated)
        self.assertEqual(new_data["personal"]["title"], text)
        new_data["personal"]["title"] = data["personal"]["title"]
        self.assertEqual(new_data, data)
        self.assertTrue(updated.endswith(source[fields["personal.title"]["end"]:]))

    def test_multiple_changes_use_original_offsets(self):
        source = '<body><h1>Title</h1><p>First.</p><p>Second.</p></body>'
        fields = HTMLFields(source).fields
        updated = patch_source(source, fields, [
            {"id": "html-0", "value": "A much longer title"},
            {"id": "html-2", "value": "Short."},
        ])
        self.assertEqual(updated, '<body><h1>A much longer title</h1><p>First.</p><p>Short.</p></body>')

    def test_math_and_dates_are_not_editable(self):
        source = '<body><p>$x^2$</p><p>\\(x\\)</p><p class="post-meta">Date</p><p>Words</p></body>'
        self.assertEqual([f["value"] for f in HTMLFields(source).fields.values()], ["Words"])

    def test_nested_blocks_do_not_overlap(self):
        source = '<body><ul><li><p>Nested</p></li><li>Plain</li></ul></body>'
        self.assertEqual([f["value"] for f in HTMLFields(source).fields.values()], ["Nested", "Plain"])

    def test_emptying_a_field_does_not_shift_later_edits(self):
        source = '<body><h1>Title</h1><p>First.</p><p>Second.</p></body>'
        cleared = patch_source(source, HTMLFields(source).fields, [{"id": "html-1", "value": ""}])
        updated = patch_source(cleared, HTMLFields(cleared).fields, [
            {"id": "html-1", "value": "New first."},
            {"id": "html-2", "value": "New second."},
        ])
        self.assertEqual(updated, '<body><h1>Title</h1><p>New first.</p><p>New second.</p></body>')

    def test_executable_markup_and_structure_changes_are_rejected(self):
        for value in ['<script>alert(1)</script>', '<img src=x onerror=alert(1)>',
                      '<a href="javascript:alert(1)">Click</a>', '<a href="java&#10;script:alert(1)">Click</a>',
                      '<span onclick="alert(1)">Text</span>', '<p>New block</p>', '<em>Unclosed', '<!-- comment -->']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_inline(value)

    def test_plain_text_and_inline_formatting_are_allowed(self):
        validate_inline('Here is <strong>text</strong>, <em>emphasis</em>, a <a href="/posts/example.html">link</a> &amp; a line<br>break.')

    def test_unknown_and_duplicate_fields_cannot_patch_source(self):
        source = '<body><p>Keep me.</p></body>'
        fields = HTMLFields(source).fields
        for edits in [[{"id": "missing", "value": "bad"}],
                      [{"id": "html-0", "value": "one"}, {"id": "html-0", "value": "two"}]]:
            with self.assertRaises(ValueError):
                patch_source(source, fields, edits)

    def test_revisions_change_on_external_edits(self):
        self.assertNotEqual(revision("original"), revision("edited"))


if __name__ == "__main__":
    unittest.main()
