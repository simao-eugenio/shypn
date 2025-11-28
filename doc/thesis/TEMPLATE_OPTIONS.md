# LaTeX Thesis Template Options

## 🎓 University Templates (Recommended First Choice)

**Before choosing a generic template, check if your university provides an official one!**

Common Portuguese universities with LaTeX templates:
- **Universidade de Lisboa**: https://github.com/ulisboa/thesis-template
- **Universidade do Porto**: https://sigarra.up.pt/feup/pt/web_page.inicial (search for "template tese latex")
- **Universidade de Coimbra**: https://www.uc.pt/fctuc/dmat/templates
- **Instituto Superior Técnico (IST)**: https://github.com/ist-thesis/ist-thesis

📌 **Action:** Please tell me your university so I can find the official template!

---

## Option 2: Popular Generic Templates

If no official template exists, here are excellent options:

### A. Classic Book Class (Simple & Clean)
**What we already created** - Standard LaTeX book class
- ✅ Simple, widely compatible
- ✅ Easy to customize
- ✅ Works with all LaTeX distributions
- ⚠️ Basic styling

### B. ClassicThesis (Elegant & Minimal)
**Link:** https://www.ctan.org/pkg/classicthesis
```bash
# Install
sudo apt-get install texlive-latex-extra
```
- ✅ Beautiful typography (inspired by Robert Bringhurst)
- ✅ Clean margins, nice fonts
- ✅ Professional appearance
- ⚠️ Opinionated design

**Preview:** https://ctan.org/tex-archive/macros/latex/contrib/classicthesis

### C. Memoir Class (Flexible)
**Link:** https://www.ctan.org/pkg/memoir
```bash
# Already included in texlive
```
- ✅ Highly customizable
- ✅ Built-in styles for thesis
- ✅ Excellent documentation
- ⚠️ More complex to configure

### D. ElegantBook (Modern)
**Link:** https://github.com/ElegantLaTeX/ElegantBook
```bash
git clone https://github.com/ElegantLaTeX/ElegantBook.git
```
- ✅ Modern, colorful design
- ✅ Good for STEM fields
- ✅ Multi-language support
- ⚠️ Less traditional

### E. Tufte-LaTeX (Unique)
**Link:** https://github.com/Tufte-LaTeX/tufte-latex
```bash
sudo apt-get install texlive-latex-extra
```
- ✅ Wide margins for notes/figures
- ✅ Distinctive, elegant
- ✅ Great for technical content
- ⚠️ Non-standard layout

---

## Option 3: Overleaf Templates

Browse 100+ thesis templates: https://www.overleaf.com/latex/templates/tagged/thesis

Popular choices:
1. **Oxford University Thesis** - Very professional
2. **Cambridge University Thesis** - Classic
3. **MIT Thesis** - Clean, technical
4. **PhD Thesis Template (Harish Kumar)** - Versatile

---

## 🎯 Recommendation Flow

```
1. Does your university have an official template?
   YES → Use that! ✅
   NO  → Go to step 2

2. Do you prefer traditional or modern style?
   Traditional → ClassicThesis or Memoir
   Modern      → ElegantBook
   Unique      → Tufte-LaTeX
   
3. Do you want to work online or locally?
   Online → Use Overleaf (web-based, easy collaboration)
   Local  → Install chosen template locally
```

---

## Quick Installation Commands

### For ClassicThesis:
```bash
sudo apt-get install texlive-latex-extra
cd ~/projetos/shypn/doc/thesis/latex
wget http://mirrors.ctan.org/macros/latex/contrib/classicthesis.zip
unzip classicthesis.zip
```

### For ElegantBook:
```bash
cd ~/projetos/shypn/doc/thesis/latex
git clone https://github.com/ElegantLaTeX/ElegantBook.git
cd ElegantBook
# Copy template files to your latex directory
```

### For Memoir (already installed):
```bash
# Just change \documentclass{book} to \documentclass{memoir}
# in thesis.tex
```

---

## ❓ What would you like to do?

**Option A:** Tell me your university → I'll find the official template

**Option B:** Choose from the options above → I'll set it up

**Option C:** Keep the simple book class we created → Ready to convert!

**Option D:** Browse Overleaf templates → I'll help you download and adapt one

**Please let me know your preference!** 🚀
