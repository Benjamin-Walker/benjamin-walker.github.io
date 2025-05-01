const siteContent = {
  personal: {
    name: "Benjamin Walker",
    title: "PhD Student in Mathematics at Oxford University",
    currentPosition:
      "I am a PhD student in Mathematics at the University of Oxford, supervised by Terry Lyons. I currently hold a Lectureship in Applied Mathematics at Balliol College.",
    researchFocus:
      "My research focuses on machine learning for sequential data, particularly in developing theoretically principled approaches to time series modeling. Additional interests include generative modelling and machine learning in healthcare.",
    education: [
      {
        degree: "DPhil Mathematics",
        institution: "University of Oxford",
        years: "2022-2025",
      },
      {
        degree: "MSc Mathematical Modelling and Scientific Computing",
        institution: "University of Oxford",
        years: "2020-2021",
        honors: "Distinction",
      },
      {
        degree: "MMaths&Physics",
        institution: "University of Manchester",
        years: "2016-2020",
        honors: "First Class Honours",
      },
    ],
    teaching: [
      "Lecturer in Applied Mathematics at Balliol College",
      "Course Author and Teacher for the MSc in MMSC Introduction to Python",
      "Supervised multiple Master's theses, including a prize-winning dissertation and work published at Machine Learning for Healthcare"
    ],
    awards: [
      "1st Place in the George B. Moody Physionet Challenge 2024",
      "Publications at top ML conferences including ICML and NeurIPS",
      "MMaths&Physics highest dissertation grade",
      "Raised £7000 for Cancer Research UK hiking 942 miles from John O'Groats to Land's End"
    ]
  },
  social: {
    twitter: "https://twitter.com/ML_BenWalker",
    bluesky: "https://bsky.app/profile/benjamincwalker.bsky.social",
    linkedin: "https://www.linkedin.com/in/benjamin-walker-3880771b9/",
    github: "https://github.com/Benjamin-Walker",
    cv: "CV.pdf",
  },
  publications: [
    {
      title: "Log Neural Controlled Differential Equations",
      conference: "International Conference on Machine Learning (ICML 2024)",
      authors: "B. Walker, A. D. McLeod, T. Qin, Y. Cheng, H. Li, T. Lyons",
      link: "https://arxiv.org/abs/2402.18512",
    },
    {
      title: "Theoretical Foundations of Deep Selective State-Space Models",
      conference: "Neural Information Processing Systems (NeurIPS 2024)",
      authors: "N. M. Cirone, A. Orvieto, B. Walker, C. Salvi, T. Lyons",
      link: "https://arxiv.org/abs/2402.19047",
    },
    {
      title: "Combining Hough Transform and Deep Learning Approaches to Reconstruct ECG Signals From Printouts",
      conference: "Computing in Cardiology (2024)",
      authors: "F. Krones, B. Walker, T. Lyons, A. Mahdi",
      link: "https://cinc.org/archives/2024/pdf/CinC2024-097.pdf",
    },
    {
      title: "ScoEHR: Generating Synthetic Electronic Health Records",
      conference: "Machine Learning for Healthcare (2023)",
      authors:
        "A. A. Naseer, B. Walker, C. Landon, A. Ambrosy, M. Fudim, N. Wysham, B. Toro, S. Swaminathan, T. Lyons",
      link: "https://proceedings.mlr.press/v219/naseer23a.html",
    },
    {
      title: "Dual Bayesian ResNet: A Deep Learning Approach to Heart Murmur Detection",
      conference: "Computing in Cardiology (2022)",
      authors: "B. Walker, F. Krones, I. Kiskin, G. Parsons, T. Lyons, A. Mahdi",
      link: "https://ieeexplore.ieee.org/abstract/document/10081848/",
    },
  ],
  projects: [
    {
      name: "Log Neural CDEs",
      description:
        "Implementation of Log Neural Controlled Differential Equations (ICML 2024)",
      link: "https://github.com/Benjamin-Walker/log-neural-cdes",
      category: "Machine Learning Research",
    },
    {
      name: "Selective SSMs and Linear NCDEs",
      description:
        "Theoretical Foundations of Deep Selective State-Space Models (NeurIPS 2024)",
      link: "https://github.com/Benjamin-Walker/selective-ssms-and-linear-cdes",
      category: "Machine Learning Research",
    },
    {
      name: "Heart Murmur Detection",
      description:
        "Dual Bayesian ResNet for Heart Murmur Detection from Phonocardiograms (CinC 2022)",
      link: "https://github.com/Benjamin-Walker/heart-murmur-detection",
      category: "Healthcare Applications",
    },
    {
      name: "Diffrax Diffusion Models",
      description: "Score-based diffusion models implemented in JAX",
      link: "https://github.com/Benjamin-Walker/diffrax-diffusion-models",
      category: "Generative Models",
    },
    {
      name: "Live Vinyl Display",
      description: "Real-time music recognition system for vinyl records",
      link: "https://github.com/Benjamin-Walker/live-vinyl-display",
      category: "Personal Projects",
    },
    {
      name: "Personal Website",
      description:
        "This website's source code with terminal-style interface and modern webpage",
      link: "https://github.com/Benjamin-Walker/benjamin-walker.github.io",
      category: "Personal Projects",
    },
  ],
  posts: [
    {
      title: "The Myth of Convenience",
      date: "2025-05-01",
      snippet: "Getting rid of my smartphone.",
      link: "posts/the-myth-of-convenience.html"
    }
  ]
};

// For browser usage
if (typeof window !== 'undefined') {
  window.siteContent = siteContent;
}

// For Node.js usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = siteContent;
}
