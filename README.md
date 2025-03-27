# ⚾ Baseball StatAI - StatMuse Mimic

Baseball StatAI is a web application that allows users to query MLB statistics using natural language, similar to StatMuse. The application is designed for the 2024 MLB season but can be scaled to include all-time statistics from 1901-2024.

## 🤩 Regular Usage is available through a web aaplication hosted by Vercel
https://baseball-statmuse.vercel.app


## 🚀 Scaling Up to All-Time Stats (1901-2024)

To expand the project to include all-time statistics, follow these steps:

1. **Clone the repository**  
   ```sh
   git clone https://github.com/ehv6/Baseball_Statmuse.git
   cd Baseball_Statmuse
   ```

2. **Download the `Main.csv` file**  
   - Visit the website link found in `index.html`.
   - Download the `Main.csv` file.

3. **Place `Main.csv` in the root directory**  
   Ensure `Main.csv` is placed in the same directory as `all_time.py`.

4. **Run the script to process all-time stats**  
   ```sh
   python all_time.py
   ```

After completing these steps, the application will support MLB statistics from 1901 to 2024.

---

## 📂 Project Structure

```
.
├── 2024_baseball.db       # SQLite database for 2024 stats
├── 2024_only.py           # Script for querying only 2024 stats
├── 2024csvs/              # CSV files for the 2024 season
│   ├── 2024allplayers.csv
│   ├── 2024batting.csv
│   ├── 2024fielding.csv
│   ├── 2024gameinfo.csv
│   ├── 2024pitching.csv
│   └── 2024teamstats.csv
├── README.md              # Project documentation
├── all_time.py            # Script for querying all-time stats
├── csvdownloads/          # CSV files for all-time data
│   ├── allplayers.csv
│   ├── batting.csv
│   ├── fielding.csv
│   ├── gameinfo.csv
│   ├── pitching.csv
│   └── teamstats.csv
├── requirements.txt       # Dependencies
├── static/                # Frontend static files
│   ├── script.js
│   └── style.css
├── templates/             # Frontend HTML templates
│   └── index.html
├── test.py                # Test script
└── vercel.json            # Vercel configuration
```

---

## 🛠️ Installation & Usage

1. **Install dependencies**  
   ```sh
   pip install -r requirements.txt
   ```

2. **Run the application**  
   ```sh
   python 2024_only.py
   ```

3. **Access the Web UI**  
   Open `index.html` in a browser or visit the deployed website on Vercel.

---

## 📊 Features

- Natural language queries for MLB stats
- 2024 season data by default
- Expandable to all-time stats (1901-2024)
- Hosted on Vercel for easy deployment

---

## 🌟 Data Source

All statistics are sourced from [RetroSheet](https://www.retrosheet.org/downloads/othercsvs.html).

---

## 🛠️ Development

- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python (Flask or standalone script)  
- **Database:** SQLite  

---

## 👨‍💻 Author

Developed by [Tushig Battulga](https://www.linkedin.com/in/tushig-battulga/).  

---

## 🌐 Deployment

The project is deployed on **Vercel**. Check `vercel.json` for deployment configurations.

---

## ⚖️ License

This project is for educational purposes. Feel free to modify and expand it!

---

Enjoy querying MLB stats like a pro! ⚾🔥

