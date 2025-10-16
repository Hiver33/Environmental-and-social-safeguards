# 🌳 Environmental-and-social-safeguards
This folder contains data projects **GriefPy** on grievances and environmental and social safeguards

#=======================================================
# 🐍 GriefPy — Grievance & Social Safeguard Dashboard
#=======================================================

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-✔️-orange)](https://streamlit.io/)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-blue?logo=streamlit)](https://share.streamlit.io/yourusername/griefpy/main/app.py)

**GriefPy** is an interactive **Python + Streamlit** dashboard to monitor, analyze, and visualize grievance management for environmental and social safeguards.  
Track status, category, and evolution of complaints with **dynamic filtering** and **clear visual indicators**.

---

## 🚀 Features

- 📅 **Dynamic filters** by year, submission type, and processing status  
- 📊 **Key metrics** in **bold, left-aligned color-coded cards**:
  - Total grievances  
  - Completed (**green**)  
  - Ongoing  
  - Unprocessed  
- 📈 **Visual analytics**:
  - **Interactive map** for grievance box locations and status tracking
  - **Bar chart**: Distribution by submission type (ascending)  
  - **Pie chart**: General progress of grievances (**fixed colors, green for Completed**)  
  - **Histogram**: Complaints by nature, color-coded by status  
  - **Bar chart**: Nature of grievances by gender (**labels show number of grievances**)  
  - **Bar chart**: Complaints by community (sorted ascending)  
  - **Pie chart**: Complaints by gender  
  - **Line chart**: Monthly/quarterly trend of grievances (Top N selectable, filterable by quarter)  
  - **Bar chart**: Average processing duration by grievance type  
- 🖥️ **Responsive layout** with optional **full-screen mode**
- 🎨 **Light/Dark theme swichting** for improved accessibility
- 📂 **Data table** displaying detailed grievance records  
- ☁️ **Ready for deployment** on Streamlit Cloud  

---

## 🎬 Live Dashboard Preview

![GriefPy Dashboard Animation](./screenshots/griefpy_demo.gif)  

> Example of interacting with filters, exploring charts, and full-screen mode.

---

## 🧩 Tech Stack

- **Python 3.9+**  
- **Streamlit**  
- **Pandas**
- **Geopandas**
- **Folium**
- **Streamlit-folium**
- **Requests**
- **Branca**
- **matplotlib**  
- **Plotly Express**  
- **OpenPyXL**

---

## ⚙️ Setup & Usage

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/GriefPy.git
   cd GriefPy
