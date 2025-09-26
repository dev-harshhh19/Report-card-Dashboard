# Student Score Card Web App

A modern, interactive web application for students to securely track, visualize, and analyze their academic progress semester by semester.  
**Built with Flask, PostgreSQL (NeonDB), Tailwind CSS, Chart.js, and a professional, accessible UI.**

# Installation Guide for Student Marks Calculator  

This guide provides detailed steps to set up and run the Student Marks Calculator project locally.

---

## Prerequisites  
Ensure you have the following installed on your system:  
1. **Python**: Version 3.7 or later. Download it from [python.org](https://www.python.org/).  
2. **Pip**: Python package manager (comes pre-installed with Python).  
3. **Git**: To clone the repository. Download from [git-scm.com](https://git-scm.com/).  
4. **NeonDB Account**: Sign up at [Neon.tech](https://neon.tech) for PostgreSQL database hosting.

---

## Installation Steps  

### 1. Clone the Repository  
Use the following commands to clone the project and navigate to the project folder:  
```bash
git clone https://github.com/dev-harshhh19/Report-card-Dashboard
cd Report-card-Dashboard
```  

### 2. Set Up a Virtual Environment (Optional but Recommended)  
A virtual environment helps isolate project dependencies.  
```bash
python -m venv venv  
source venv/bin/activate  # For Linux/Mac  
venv\Scripts\activate     # For Windows  
```  

### 3. Set Up Database Configuration
Configure your PostgreSQL database connection:
```bash
cp .env.example .env
# Edit .env file with your NeonDB connection string
```

Update the `DATABASE_URL` in your `.env` file with your actual NeonDB connection string.

### 4. Install Required Dependencies  
Install all necessary Python libraries using the `requirements.txt` file:  
```bash
pip install -r requirements.txt
```  

### 5. Run the Application  
Start the application by running the main file:  
```bash
python Report-card-Dashboard.py
```  

---

## Accessing the Application  

1. Open your web browser.  
2. Navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000).  

---

## Project Structure  

- **`Report-card-Dashboard.py`**: The main Python file that runs the Flask application with PostgreSQL support.  
- **`models.py`**: Database models for Users, Students, and Semesters using SQLAlchemy.
- **`database.py`**: Database configuration and connection management.
- **`templates/`**: Contains HTML files for the front-end.  
- **`static/`**: Contains CSS and JavaScript files for styling and interactivity.  
- **`requirements.txt`**: Lists all required Python packages including database dependencies.
- **`.env`**: Environment configuration file (create from .env.example).  

---

## Troubleshooting  

- **Missing Dependencies**: Run `pip install -r requirements.txt` again.  
- **Port Errors**: Ensure no other application is using port 5000.  

---

## Contribution  

We welcome contributions! Follow these steps:  
1. Fork the repository.  
2. Create a new branch (`git checkout -b feature-branch`).  
3. Commit changes and push them (`git push origin feature-branch`).  
4. Submit a pull request.  

---

Enjoy building and enhancing this project!
---
## 💰 You can help me by Donating
  [![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/dev.harhhh) [![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/HarshadNikam388) 
