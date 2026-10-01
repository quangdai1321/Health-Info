"""
Ve so do kien truc 4 tang cho manuscript (thay the file draw.io bi mat).
Chi tieng Anh, dung cho ban nop. Sua 2 loi da biet trong CONTEXT.md:
  - Khong lap chu thich don vi (vd 'g/L') hai lan.
  - Nhanh "No" chi di sang "Regenerate / fallback template", roi net dut
    quay ve Layer 3 -- khong di thang len "Verified text".
Ban compact: giu ty le gan vuong de figure khong bi day sang trang rieng.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FIG_W, FIG_H = 6.8, 6.55
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")

BOX_W = 5.4
X0 = (FIG_W - BOX_W) / 2

COLOR_NOLLM = "#dbe7f5"
COLOR_LLM = "#fde7cf"
COLOR_EDGE = "#2b3a55"
COLOR_DECISION = "#f2f2f2"

def box(y, h, title, lines, color, x=X0, w=BOX_W, fontsize_title=9.5, fontsize_body=8):
    b = FancyBboxPatch((x, y), w, h,
                        boxstyle="round,pad=0.02,rounding_size=0.07",
                        linewidth=1.3, edgecolor=COLOR_EDGE, facecolor=color)
    ax.add_patch(b)
    ax.text(x + w / 2, y + h - 0.19, title, ha="center", va="top",
            fontsize=fontsize_title, fontweight="bold", color=COLOR_EDGE)
    body = "\n".join(lines)
    ax.text(x + w / 2, y + h - 0.40, body, ha="center", va="top",
            fontsize=fontsize_body, color="#1a1a1a", linespacing=1.35)
    return b

def arrow(x, y0, y1, lw=1.4, color=COLOR_EDGE, ls="-"):
    a = FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=11,
                         linewidth=lw, color=color, linestyle=ls)
    ax.add_patch(a)

GAP = 0.14
H_MAIN = 0.72
y = FIG_H - 0.40
box(y, 0.36, "Vietnamese CBC panel (raw values, free-text names, units)", [],
    COLOR_DECISION, fontsize_title=7.6)
y -= GAP + H_MAIN
y1 = y
box(y1, H_MAIN, "Layer 1 -- Name & Unit Normalisation  (no LLM)",
    ["Alias -> canonical code (NEUT%, % Neu -> same code)",
     "Convert to canonical unit; REFUSE if unit unknown/missing"],
    COLOR_NOLLM)
y -= GAP + H_MAIN
y2 = y
box(y2, H_MAIN, "Layer 2 -- Rule-Based Classification  (no LLM)",
    ["Compare to reference interval -> normal / monitor / seek care",
     "threshold = severity_factor x (high - low), per analyte"],
    COLOR_NOLLM)
y -= GAP + H_MAIN
y3 = y
box(y3, H_MAIN, "Layer 3 -- Constrained Generation  (LLM)",
    ["Model receives pre-assigned labels, not raw judgement",
     "Input / content / JSON-schema constraints"],
    COLOR_LLM)
y -= GAP + H_MAIN
y4 = y
box(y4, H_MAIN, "Layer 4 -- Post-Generation Validation  (no LLM)",
    ["Checks direction, forbidden terms, coverage, false reassurance",
     "against the Layer 2 labels"],
    COLOR_NOLLM)

y -= GAP + 0.5
y_dec = y
dec_w, dec_h = 2.5, 0.5
dec_x = X0 + (BOX_W - dec_w) / 2
dec = FancyBboxPatch((dec_x, y_dec), dec_w, dec_h,
                      boxstyle="round,pad=0.02,rounding_size=0.25",
                      linewidth=1.3, edgecolor=COLOR_EDGE, facecolor=COLOR_DECISION)
ax.add_patch(dec)
ax.text(dec_x + dec_w / 2, y_dec + dec_h / 2, "Passes validation?",
        ha="center", va="center", fontsize=8.5, fontweight="bold", color=COLOR_EDGE)

y -= GAP + 0.6
y_leaf = y
leaf_w = 2.5
yes_x = X0
no_x = X0 + BOX_W - leaf_w
box(y_leaf, 0.6, "Verified text", ["Returned to patient"], "#dff5df",
    x=yes_x, w=leaf_w, fontsize_title=8.5, fontsize_body=7.6)
box(y_leaf, 0.6, "Regenerate / fixed-template\nfallback (after retry limit)", [],
    "#f9dede", x=no_x, w=leaf_w, fontsize_title=8, fontsize_body=7.6)

# ---- arrows ----
xc = X0 + BOX_W / 2
input_bottom = FIG_H - 0.40
arrow(xc, input_bottom, y1 + H_MAIN)
arrow(xc, y1, y2 + H_MAIN)
arrow(xc, y2, y3 + H_MAIN)
arrow(xc, y3, y4 + H_MAIN)
arrow(xc, y4, y_dec + dec_h)

yes_cx = yes_x + leaf_w / 2
no_cx = no_x + leaf_w / 2
a_yes = FancyArrowPatch((dec_x + 0.25, y_dec), (yes_cx, y_leaf + 0.6),
                         connectionstyle="arc3,rad=0.15",
                         arrowstyle="-|>", mutation_scale=11, linewidth=1.4, color="#1b7a1b")
ax.add_patch(a_yes)
ax.text(dec_x - 0.08, y_dec - 0.22, "Yes", ha="right", va="center",
        fontsize=8, fontweight="bold", color="#1b7a1b")

a_no = FancyArrowPatch((dec_x + dec_w - 0.25, y_dec), (no_cx, y_leaf + 0.6),
                        connectionstyle="arc3,rad=-0.15",
                        arrowstyle="-|>", mutation_scale=11, linewidth=1.4, color="#a11a1a")
ax.add_patch(a_no)
ax.text(dec_x + dec_w + 0.08, y_dec - 0.22, "No", ha="left", va="center",
        fontsize=8, fontweight="bold", color="#a11a1a")

fb = FancyArrowPatch((no_x + leaf_w - 0.04, y_leaf + 0.6), (no_x + leaf_w - 0.04, y3 + H_MAIN),
                      arrowstyle="-|>", mutation_scale=10, linewidth=1.2,
                      color="#a11a1a", linestyle=(0, (4, 2.5)))
ax.add_patch(fb)
ax.text(no_x + leaf_w + 0.06, (y_leaf + y3 + H_MAIN) / 2, "retry",
        ha="left", va="center", fontsize=6.8, color="#a11a1a", style="italic")

plt.tight_layout(pad=0.12)
plt.savefig("architecture.png", dpi=220)
print("saved architecture.png, figsize=", FIG_W, FIG_H)
