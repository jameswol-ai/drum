# DRUM Studio 🏗️

**Professional Structural Analysis Workstation** built with Streamlit.

DRUM Studio provides structural engineers with an interactive platform to design building floor plans, perform structural calculations, and manage projects—all in a single web application.

---

## ✨ Features

- **User authentication** with secure password hashing (werkzeug)
- **Project dashboard** with:
  - 2D floor plan editor (add/remove/modify rooms)
  - Interactive 3D model (Three.js)
  - Grid overlay, north arrow, and dimension labels
  - Room nudging (arrow-key style movement)
  - Color picker for each room
  - Live area breakdown per room
  - Cost & material estimate
  - Project comparison
  - Export to SVG and PDF
- **Structural Analysis Workstation** with calculators for:
  - Reinforced concrete and steel beams
  - RC columns
  - Slab thickness estimation
  - Pad footing sizing
  - Walls & finishes (weights, U-values, sound reduction)
  - Pile capacity (simplified EC7)
  - Prestressed concrete stress checks
  - Retaining wall stability
  - Truss solver (placeholder)
- **Unit conversion** – metric/imperial toggle across all inputs/outputs
- **Random plan generator** – instantly create a multi‑room layout
- **Archive view** to browse saved projects

---

## 🚀 Installation (Local)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/drum.git
   cd drum