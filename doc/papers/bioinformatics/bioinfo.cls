%% bioinfo.cls - Version 1.0
%% Based on Oxford Bioinformatics LaTeX template
%% Simplified two-column class file

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{bioinfo}[2025/01/01 v1.0 Bioinformatics class]

% Base class
\LoadClass[twocolumn,twoside,9pt]{extarticle}

% Packages
\RequirePackage[a4paper,margin=2cm,columnsep=0.6cm]{geometry}
\RequirePackage{times}
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{fancyhdr}
\RequirePackage{caption}
\RequirePackage{booktabs}
\RequirePackage{hyperref}

% Font settings
\renewcommand{\normalsize}{\fontsize{9}{11}\selectfont}
\renewcommand{\small}{\fontsize{8}{10}\selectfont}
\renewcommand{\footnotesize}{\fontsize{7}{9}\selectfont}
\renewcommand{\large}{\fontsize{10}{12}\selectfont}
\renewcommand{\Large}{\fontsize{12}{14}\selectfont}
\renewcommand{\LARGE}{\fontsize{14}{18}\selectfont}

% Counters
\newcounter{firstpage}
\setcounter{firstpage}{1}

% Commands
\def\@copyrightyear{2025}
\def\@pubyear{2025}
\def\@access{}
\def\@appnotes{}
\def\@subtitle{}
\def\@corresp{}
\def\@history{}
\def\@editor{}

\newcommand{\copyrightyear}[1]{\gdef\@copyrightyear{#1}}
\newcommand{\pubyear}[1]{\gdef\@pubyear{#1}}
\newcommand{\access}[1]{\gdef\@access{#1}}
\newcommand{\appnotes}[1]{\gdef\@appnotes{#1}}
\newcommand{\subtitle}[1]{\gdef\@subtitle{#1}}
\newcommand{\corresp}[1]{\gdef\@corresp{#1}}
\newcommand{\history}[1]{\gdef\@history{#1}}
\newcommand{\editor}[1]{\gdef\@editor{#1}}
\newcommand{\firstpage}[1]{\setcounter{firstpage}{#1}}
\newcommand{\address}[1]{\gdef\@address{#1}}

% Define sfb command for small bold sans-serif
\DeclareTextFontCommand{\sfb}{\sffamily\bfseries}

% Title formatting
\renewcommand{\maketitle}{%
  \twocolumn[%
    \begin{@twocolumnfalse}%
      \vspace*{-1cm}%
      % Header info
      {\small\textit{Bioinformatics}, \@copyrightyear, \arabic{firstpage}--\arabic{firstpage}}
      
      {\small doi: 10.1093/bioinformatics/xxxxx}
      
      {\small\@access}
      
      \vspace{0.3cm}
      
      % Article type
      {\Large\bfseries\@appnotes}
      
      \vspace{0.2cm}
      
      % Subtitle
      {\large\@subtitle}
      
      \vspace{0.3cm}
      
      % Title
      {\LARGE\bfseries\@title}
      
      \vspace{0.4cm}
      
      % Authors
      {\large\@author}
      
      \vspace{0.2cm}
      
      % Address
      {\small\@address}
      
      \vspace{0.2cm}
      
      % Correspondence
      \ifx\@corresp\@empty\else%
        {\small\@corresp}
        
        \vspace{0.1cm}
      \fi
      
      % History
      \ifx\@history\@empty\else%
        {\small\@history}
        
        \vspace{0.1cm}
      \fi
      
      % Editor
      \ifx\@editor\@empty\else%
        {\small\@editor}
        
        \vspace{0.2cm}
      \fi
      
      % Abstract
      \ifx\@abstract\@empty\else%
        \begin{minipage}{\textwidth}%
          \small
          \@abstract
        \end{minipage}
        
        \vspace{0.5cm}
      \fi
      
    \end{@twocolumnfalse}%
  ]%
}

% Abstract
\renewcommand{\abstract}[1]{\gdef\@abstract{#1}}
\gdef\@abstract{}

% Section formatting
\renewcommand{\section}{%
  \@startsection{section}{1}{\z@}%
  {-12pt plus -3pt minus -2pt}%
  {6pt plus 2pt minus 1pt}%
  {\large\bfseries}%
}

\renewcommand{\subsection}{%
  \@startsection{subsection}{2}{\z@}%
  {-10pt plus -2pt minus -1pt}%
  {4pt plus 1pt minus 0.5pt}%
  {\normalsize\bfseries}%
}

% Caption formatting
\captionsetup{
  font=small,
  labelfont=bf,
  skip=6pt
}

% Table environment
\newcommand{\processtable}[3]{%
  \caption{#1}%
  \centering%
  #2%
  \ifx\relax#3\relax\else%
    \vspace{6pt}\\%
    \parbox{\columnwidth}{\small #3}%
  \fi%
}

% Headers and footers
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE,RO]{\small\thepage}
\fancyhead[LO,RE]{\small\textit{Author et al.}}
\renewcommand{\headrulewidth}{0pt}

% Hyperref settings
\hypersetup{
  colorlinks=true,
  linkcolor=blue,
  citecolor=blue,
  urlcolor=blue
}

\endinput
