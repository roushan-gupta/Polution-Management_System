# 🌍 Pollution Management System

A comprehensive real-time air quality monitoring and management system with modern UI, interactive maps, and intelligent data fallback mechanisms.

## ✨ Features

### 🎨 Modern UI
- **Glassmorphism Design**: Beautiful gradient backgrounds with glass-effect cards
- **Mobile-First**: Fully responsive design ready for Flutter migration
- **Smooth Animations**: CSS animations for enhanced user experience
- **No-Login Public Access**: Public AQI dashboard accessible without authentication

### 📊 Air Quality Monitoring
- **Multi-Source Data**: OpenAQ API + WAQI integration (when configured) + Database fallback
- **Real-Time Updates**: Live AQI data with PM2.5 and PM10 measurements
- **Smart Fallback**: 3-tier system ensures data availability
- **Distance Calculation**: Haversine formula finds nearest monitoring stations

### 🗺️ Interactive Maps
- **Leaflet Integration**: Color-coded AQI markers on interactive map
- **Geocoding Search**: Dynamic location search powered by OpenStreetMap Nominatim
- **Location Detection**: Automatic user location detection
- **Visual Categories**: AQI color scheme (Good → Severe)

### 🔐 User Management
- **Role-Based Access**: Citizen and Authority roles
- **OTP Verification**: Secure registration with phone OTP
- **Incident Reporting**: Citizens can report pollution incidents
- **Admin Panel**: Authority dashboard for monitoring

## 📁 Project Structure

```
Pollution Management System/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── config.py              # Configuration settings
│   ├── db.py                  # Database connection
│   ├── routes/
│   │   ├── aqi.py            # AQI endpoints with 3-tier fallback
│   │   ├── auth.py           # Authentication & registration
│   │   ├── incident.py       # Incident reporting
│   │   ├── location.py       # Location management
│   │   └── notification.py   # Notification system
│   ├── models/               # Database models
│   └── services/             # Business logic services
├── frontend/
│   ├── index.html            # Modern login page
│   ├── register.html         # Registration with OTP
│   ├── public_aqi.html       # Public AQI dashboard (no login)
│   ├── citizen.html          # Citizen dashboard
│   ├── authority.html        # Authority dashboard
│   ├── css/
│   │   └── style.css        # 800+ lines modern CSS
│   └── js/
│       ├── public-aqi-dashboard.js  # Public dashboard logic
│       ├── login.js                 # Login functionality
│       └── register.js              # Registration flow
├── ml/
│   ├── train_model.ipynb     # ML model training
│   └── predict.py            # Prediction service
├── database/
│   └── schema.sql            # MySQL database schema
├── REAL_AQI_INTEGRATION_GUIDE.md  # Guide for real data setup
└── README.md                  # This file

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Modern web browser
- Internet connection (for external APIs)

### Installation

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd "Pollution Management System"
   ```

2. **Setup Virtual Environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure Database**
   ```sql
   -- Create database
   CREATE DATABASE pollution_management;
   
   -- Import schema
   mysql -u root -p pollution_management < database/schema.sql
   ```

5. **Update Configuration**
   Edit `backend/config.py`:
   ```python
   MYSQL_HOST = "localhost"
   MYSQL_USER = "your_username"
   MYSQL_PASSWORD = "your_password"
   MYSQL_DB = "pollution_management"
   ```

6. **Create Admin User** (Optional)
   ```bash
   cd backend
   python create_admin.py
   ```

7. **Run Application**
   ```bash
   python app.py
   ```

8. **Access Application**
   - Public Dashboard: http://127.0.0.1:5000/public_aqi.html
   - Login: http://127.0.0.1:5000/
   - API Docs: http://127.0.0.1:5000/api/docs

## 📊 Current Data Status

⚠️ **Demo Mode Active**: Currently showing sample test data

To integrate **real-time AQI data**, see: [REAL_AQI_INTEGRATION_GUIDE.md](REAL_AQI_INTEGRATION_GUIDE.md)

### Data Sources:
1. **OpenAQ API** ✅ (Limited coverage)
2. **WAQI API** 🔄 (Needs API key - [Get free key](https://aqicn.org/api/))
3. **Database Fallback** ✅ (Test data)

## 🔧 API Endpoints

### Public Endpoints (No Auth Required)
```
GET /aqi/current?lat={lat}&lng={lng}  # Get current location AQI
GET /aqi/all                           # List all monitoring locations
POST /aqi/populate-test-data           # Generate test data (dev only)
```

### Authenticated Endpoints
```
POST /auth/register                    # Register new user
POST /auth/login                       # User login
GET /locations                         # Get all locations
POST /incident/report                  # Report pollution incident
GET /notifications                     # Get user notifications
```

## 🎨 UI Components

### Color Scheme
- **Good (0-50)**: Green gradient
- **Satisfactory (51-100)**: Yellow gradient
- **Moderate (101-200)**: Orange gradient
- **Poor (201-300)**: Red gradient 
- **Very Poor (301-400)**: Purple gradient
- **Severe (401+)**: Maroon gradient

### Animations
- Gradient background shift
- Slide-up fade-in effects
- Loading spinners
- Pulse markers for search
- Number counter animations

## 🔐 User Roles

### Citizen
- View AQI data
- Report incidents
- Receive notifications
- Track personal data

### Authority
- Monitor all locations
- Manage incidents
- Send alerts
- View analytics

## 🧪 Testing

### Populate Test Data
```bash
curl -X POST http://127.0.0.1:5000/aqi/populate-test-data
```

### Test Current Location AQI
```bash
# Test with Mumbai coordinates
curl "http://127.0.0.1:5000/aqi/current?lat=19.0760&lng=72.8777"
```

### Test Search
1. Open public_aqi.html
2. Type any city name (e.g., "Kochi", "Delhi", "London")
3. Select from autocomplete suggestions
4. View AQI data for that location

## 📱 Mobile Ready

The UI is designed mobile-first and ready for Flutter migration:
- Responsive breakpoints (320px → 1920px)
- Touch-friendly buttons and inputs
- Optimized for small screens
- Fast loading and smooth animations

## 🛠️ Tech Stack

### Backend
- **Flask 3.1.2**: Web framework
- **MySQL**: Database
- **Flask-CORS**: Cross-origin support
- **Requests**: HTTP library for APIs

### Frontend
- **HTML5 & CSS3**: Modern markup
- **Bootstrap 5.3.2**: UI framework
- **Leaflet.js 1.9.4**: Interactive maps
- **Font Awesome 6.4.0**: Icons
- **Vanilla JavaScript**: No heavy frameworks

### APIs
- **OpenAQ v2**: Air quality data
- **WAQI**: Real-time AQI (optional)
- **Nominatim**: Geocoding search

## 📚 Documentation

- [Real AQI Integration Guide](REAL_AQI_INTEGRATION_GUIDE.md) - How to setup real-time data
- [API Documentation](docs/API.md) - Complete API reference (coming soon)
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment (coming soon)

## 🐛 Known Issues

1. **Test Data vs Real Data**: Currently showing random test data. See integration guide for real data setup.
2. **OpenAQ Coverage**: Limited monitoring stations in some regions.
3. **Rate Limiting**: Nominatim geocoding has rate limits (1 request/second).

## 🔮 Future Enhancements

- [ ] Get WAQI API key for real-time data
- [ ] Add data caching layer (Redis)
- [ ] Historical data charts
- [ ] Predictive models using ML
- [ ] Push notifications
- [ ] Mobile app (Flutter)
- [ ] Multi-language support
- [ ] Export data to CSV/PDF

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Team

- Project developed as part of pollution management initiatives
- UI/UX redesign: Modern glassmorphism implementation
- API Integration: Multi-source data architecture

## 📞 Support

For issues or questions:
- Check [REAL_AQI_INTEGRATION_GUIDE.md](REAL_AQI_INTEGRATION_GUIDE.md) for data integration help
- Open an issue on GitHub
- Contact the development team

---

**Status**: ✅ Demo Version with Test Data | 🔄 Real-time Integration Pending
**Last Updated**: February 10, 2026
**Version**: 2.0.0 (Modern UI Update)
