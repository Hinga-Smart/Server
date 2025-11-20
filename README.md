
#  HingaSmart Backend monitoring server

This backend supports multiple sensors, real-time data collection, and easy integration with a modern frontend dashboard.

---

## **Key Features & Improvements**

### 1. Multi-Sensor Support

* Each sensor has a unique `sensor_id` and `sensor_name`.
* Track multiple sensors in different locations (greenhouse, farm zones, etc.).
* Only active sensors can send data to the backend, ensuring data integrity.

### 2. Two-Table Supabase Database

**Sensors Table**

| Column       | Type      | Notes                                |
| ------------ | --------- | ------------------------------------ |
| sensor_id    | int       | Primary key                          |
| sensor_name  | text      | Friendly name (e.g., “Greenhouse 1”) |
| location     | text      | Optional GPS or section              |
| installed_at | timestamp | Deployment date                      |
| active       | boolean   | Is the sensor active                 |

**Moisture Records Table**

| Column    | Type      | Notes                           |
| --------- | --------- | ------------------------------- |
| id        | bigint    | Primary key                     |
| timestamp | timestamp | UTC reading time                |
| sensor_id | int       | Foreign key → sensors.sensor_id |
| moisture  | integer   | Soil moisture reading           |
| state     | text      | DRY / MODERATE / WET            |

### 3. Sensor Management API

* **Add sensor:** `POST /sensor/add`
* **Update sensor info:** `PUT /sensor/update/<sensor_id>`
* **List all sensors:** `GET /sensors`

### 4. Moisture Data API

* **Record moisture reading:** `POST /data`
* **Fetch latest reading:** `GET /latest?sensor_id=<id>`
* **Fetch all readings:** `GET /all?sensor_id=<id>`

### 5. Automatic State Classification

* Based on soil moisture value:

  * `< DRY_THRESHOLD` → `DRY`
  * `> WET_THRESHOLD` → `WET`
  * Else → `MODERATE`

### 6. Serverless Deployment Ready

* Fully compatible with **Vercel serverless functions**.
* No local database required — all data stored in Supabase.
* Scalable, low-maintenance, and free hosting options.

### 7. Error Logging

* All errors are logged locally in `error_log.txt` for debugging.
* Ensures robust monitoring of API failures.

---

## **Technology Stack**

* **Backend:** Python 3, Flask
* **Database:** Supabase (PostgreSQL)
* **Deployment:** Vercel (serverless)
* **Environment Management:** `python-dotenv`

---

## **Getting Started**

### 1. Clone Repository

```bash
git clone https://github.com/Hinga-Smart/Server.git
cd Server
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables

Create a `.env` file with:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
PORT=1000
```

### 4. Run Locally

```bash
python api/index.py
```

### 5. Deploy to Vercel

* Install Vercel CLI: `npm install -g vercel`
* Link project: `vercel link`
* Deploy: `vercel --prod`

Your API will be available at `https://<project-name>.vercel.app/`.

---

## **Usage Examples**

### Add a Sensor

```bash
POST /sensor/add
{
  "sensor_id": 1,
  "sensor_name": "Greenhouse 1",
  "location": "Zone A"
}
```

### Record Moisture

```bash
POST /data
{
  "sensor_id": 1,
  "moisture": 512
}
```

### Get Latest Reading

```bash
GET /latest?sensor_id=1
```

### Get All Readings

```bash
GET /all?sensor_id=1
```

---

## **Improvements Over Original Version**

1. Replaced single-sensor Excel storage with **Supabase multi-sensor DB**.
2. Added **sensor validation** and management routes.
3. Backend now **serverless-ready** for Vercel deployment.
4. Improved **scalability**, **tracking**, and **state classification**.
5. Supports multiple sensors sending data simultaneously from different locations.
