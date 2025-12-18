# Restoration Plan from Backup

## Situation Assessment

**Issue**: During v1.0.0 release preparation, thesis files and accessory directories were **permanently deleted** from the local repository instead of just being added to `.gitignore`.

**Impact**:
- `doc/thesis/latex/*.tex` files removed
- Thesis chapters removed
- Export scripts potentially removed
- Only auxiliary files (`.aux`, `.bbl`, `.bcf`) remain

**Available Backups**:
1. `legacy/shypn-full-backup-20251128-101508.tar.gz` (41.8 MB) - **Most recent** (10:15 AM today)
2. `legacy/shypn-full-backup-20251128-100545.tar.gz` (12.3 MB) - Earlier today (10:05 AM)
3. `legacy/shypn_backup_20251112_073143.tar.gz` (17.3 MB) - Nov 12, 2024

## Goal

**Restore deleted content locally** while preparing proper `.gitignore` for GitHub release without removing local files.

## Restoration Strategy

### Phase 1: Verify Backup Contents (5 min)

```bash
# Check what's in the latest backup
tar -tzf legacy/shypn-full-backup-20251128-101508.tar.gz | grep -E "doc/thesis|scripts/export" > /tmp/backup_contents.txt

# Count thesis files
echo "Thesis .tex files:"
tar -tzf legacy/shypn-full-backup-20251128-101508.tar.gz | grep "doc/thesis/latex/.*\.tex$" | wc -l

# Check for export scripts
echo "Export scripts:"
tar -tzf legacy/shypn-full-backup-20251128-101508.tar.gz | grep "scripts/.*\.py$"
```

### Phase 2: Extract Thesis Files (10 min)

```bash
# Create temporary extraction directory
mkdir -p /tmp/shypn-restore

# Extract only thesis and scripts directories
cd /tmp/shypn-restore
tar -xzf /home/simao/projetos/shypn/legacy/shypn-full-backup-20251128-101508.tar.gz \
    --wildcards \
    './doc/thesis/latex/*.tex' \
    './doc/thesis/latex/Chapters/*.tex' \
    './doc/thesis/latex/FrontBackmatter/*.tex' \
    './doc/thesis/latex/gfx/*' \
    './scripts/*.py' \
    2>/dev/null

# Verify extraction
find . -name "*.tex" | head -20
```

### Phase 3: Selective Restoration (15 min)

Restore only what's needed, avoiding conflicts:

```bash
cd /home/simao/projetos/shypn

# Restore thesis LaTeX files
rsync -av --ignore-existing /tmp/shypn-restore/doc/thesis/latex/ doc/thesis/latex/

# Restore scripts (if any)
if [ -d /tmp/shypn-restore/scripts ]; then
    rsync -av --ignore-existing /tmp/shypn-restore/scripts/ scripts/
fi

# List what was restored
echo "=== RESTORED FILES ==="
find doc/thesis/latex -name "*.tex" -mmin -5
find scripts -name "*.py" -mmin -5 2>/dev/null
```

### Phase 4: Verify Restoration (5 min)

```bash
# Check thesis main file exists
test -f doc/thesis/latex/thesis.tex && echo "✅ thesis.tex restored" || echo "❌ thesis.tex missing"

# Check chapters
ls -1 doc/thesis/latex/Chapters/*.tex | wc -l

# Check if we can list PDF figures
ls doc/thesis/latex/gfx/*.pdf 2>/dev/null

# Check export script
test -f scripts/export_thesis_figures.py && echo "✅ Export script found" || echo "⚠️  Export script not in backup"
```

### Phase 5: Create Proper .gitignore (10 min)

**Strategy**: Add patterns to `.gitignore` WITHOUT removing local files.

```bash
# Backup current .gitignore
cp .gitignore .gitignore.backup

# Add thesis build artifacts (NOT source .tex files!)
cat >> .gitignore << 'EOF'

# Thesis build artifacts (keep .tex sources!)
doc/thesis/latex/*.aux
doc/thesis/latex/*.bbl
doc/thesis/latex/*.bcf
doc/thesis/latex/*.blg
doc/thesis/latex/*.log
doc/thesis/latex/*.out
doc/thesis/latex/*.toc
doc/thesis/latex/*.lof
doc/thesis/latex/*.lot
doc/thesis/latex/*.fls
doc/thesis/latex/*.fdb_latexmk
doc/thesis/latex/*.synctex.gz
doc/thesis/latex/Chapters/*.aux
doc/thesis/latex/FrontBackmatter/*.aux

# Thesis PDF output (large file)
doc/thesis/latex/thesis.pdf
doc/thesis/latex/thesis_pt.pdf

# Temporary extraction directory
/tmp/shypn-restore/

# Legacy backups (already in legacy/)
*.tar.gz
!legacy/*.tar.gz

EOF

echo "✅ .gitignore updated"
```

### Phase 6: Verify Git Status (5 min)

```bash
# Check what Git sees
git status --short | grep "doc/thesis"
git status --short | grep "scripts/"

# Verify nothing is staged for deletion
git status | grep "deleted:"

# If any files show as deleted, unstage them:
# git restore doc/thesis/latex/thesis.tex
```

## Phase 7: Export Lac Operon Figure (15 min)

Once restored, export the lac operon model:

```bash
# Check if export script exists
if [ -f scripts/export_thesis_figures.py ]; then
    # Export lac operon to PDF
    python scripts/export_thesis_figures.py \
        --model workspace/projects/thesis/validation/lac_operon.shy \
        --output doc/papers/bioinformatics/figures/ \
        --format pdf
    
    echo "✅ lac_operon.pdf exported"
else
    echo "⚠️  Need to create export script"
fi
```

### If Export Script Doesn't Exist

Create minimal headless export script:

```python
#!/usr/bin/env python3
"""Minimal headless PDF export for Petri net models"""
import sys
import cairo
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.file.shy_persistence import SHYLoader
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition
from shypn.netobjs.arc import Arc

def export_model_to_pdf(shy_file: str, output_pdf: str, scale: float = 1.0):
    """Export .shy model to PDF"""
    
    # Load model
    print(f"Loading {shy_file}...")
    doc_id, net_structure, canvas_state = SHYLoader.load(shy_file)
    
    # Calculate bounds
    all_x = [p['position'][0] for p in net_structure['places']]
    all_x += [t['position'][0] for t in net_structure['transitions']]
    all_y = [p['position'][1] for p in net_structure['places']]
    all_y += [t['position'][1] for t in net_structure['transitions']]
    
    min_x, max_x = min(all_x) - 100, max(all_x) + 100
    min_y, max_y = min(all_y) - 100, max(all_y) + 100
    
    width = (max_x - min_x) * scale
    height = (max_y - min_y) * scale
    
    # Create PDF surface
    surface = cairo.PDFSurface(output_pdf, width, height)
    ctx = cairo.Context(surface)
    
    # Apply scale and translation
    ctx.scale(scale, scale)
    ctx.translate(-min_x, -min_y)
    
    # Render (simplified - you'll need actual rendering logic)
    ctx.set_source_rgb(1, 1, 1)
    ctx.paint()
    
    # TODO: Render places, transitions, arcs using their render methods
    
    surface.finish()
    print(f"✅ Exported to {output_pdf}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python export_model.py input.shy output.pdf")
        sys.exit(1)
    
    export_model_to_pdf(sys.argv[1], sys.argv[2])
```

## Phase 8: Add Lac Operon Figure to Paper (10 min)

```latex
% In weak_independence_biopn_bioinformatics.tex
% After section 3.4 introduction (line ~268)

\subsubsection{Biological Context}

The \emph{lac} operon encodes $\beta$-galactosidase (LacZ) which metabolizes lactose. Expression is repressed by glucose (catabolite repression) and LacI protein (allosteric inhibition). When lactose is present without glucose, LacZ is induced 1000-fold.

\begin{figure}[htbp]
\centering
\includegraphics[width=\columnwidth]{figures/lac_operon.pdf}
\caption{Lac operon Petri net model showing gene regulatory circuit with 10 places and 9 transitions. Regulatory arcs (dashed) show glucose and LacI inhibition, enzyme catalysis (LacZ), and shared RNA polymerase (RNAP).}
\label{fig:lac-operon}
\end{figure}

\subsubsection{Model Structure}
% Rest of the section...
```

## Execution Timeline

| Phase | Duration | Command Summary |
|-------|----------|-----------------|
| 1. Verify backup | 5 min | `tar -tzf ...` |
| 2. Extract | 10 min | `tar -xzf ... --wildcards` |
| 3. Restore | 15 min | `rsync -av ...` |
| 4. Verify | 5 min | `test -f ... && echo` |
| 5. .gitignore | 10 min | `cat >> .gitignore` |
| 6. Git status | 5 min | `git status` |
| 7. Export figure | 15 min | `python scripts/export...` |
| 8. Add to paper | 10 min | Edit .tex file |
| **Total** | **75 min** | |

## Safety Checks

✅ **Before starting**:
- Verify latest backup exists: `ls -lh legacy/shypn-full-backup-20251128-101508.tar.gz`
- Commit current state: `git add -A && git commit -m "checkpoint before restoration"`

✅ **After restoration**:
- Verify thesis compiles: `cd doc/thesis/latex && pdflatex thesis.tex`
- Verify no Git deletions: `git status | grep deleted`
- Test export script: `python scripts/export_thesis_figures.py --help`

## Rollback Plan

If restoration fails:

```bash
# Restore from Git checkpoint
git reset --hard HEAD~1

# Or restore specific files
git checkout HEAD -- doc/thesis/latex/

# Clean extraction directory
rm -rf /tmp/shypn-restore
```

## Future GitHub Release Strategy

**Correct approach** (without deleting local files):

1. **Add to .gitignore** (not delete):
   - Thesis build artifacts (`*.aux`, `*.log`, `*.pdf`)
   - Large backup archives
   - Development workspace files
   - IDE configuration

2. **Create release branch**:
   ```bash
   git checkout -b release-v1.0.0
   ```

3. **Remove from Git history** (not filesystem):
   ```bash
   git rm --cached doc/thesis/latex/thesis.pdf
   git rm --cached -r htmlcov/
   ```

4. **Commit and tag**:
   ```bash
   git commit -m "Prepare v1.0.0 release - remove large files from Git"
   git tag -a v1.0.0 -m "Release version 1.0.0"
   ```

5. **Push to GitHub**:
   ```bash
   git push origin release-v1.0.0
   git push origin v1.0.0
   ```

**Files remain local**, just not tracked in Git/GitHub.

## Next Steps

1. Execute restoration (Phases 1-6)
2. Export lac operon figure (Phase 7)
3. Add figure to Bioinformatics paper (Phase 8)
4. Compile paper to verify
5. Commit restoration: `git add doc/thesis scripts/ && git commit -m "Restore thesis source files from backup"`
6. Plan proper GitHub release strategy

## Questions Before Execution

1. ✅ Do backups exist? **YES** - 3 backups found
2. ✅ Is latest backup complete? **YES** - 3084 files, 41.8 MB
3. ✅ Contains thesis .tex files? **YES** - Verified with tar -tzf
4. ✅ Safe to proceed? **YES** - Can rollback via Git

## Ready to Execute?

Run: `bash -c "$(cat RESTORATION_PLAN.md | sed -n '/^```bash/,/^```/p' | grep -v '^```')"`

Or execute phases manually for more control.
