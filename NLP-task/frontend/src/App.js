import React, { useState } from "react";
import axios from "axios";
import { Pie, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

function App() {
  const [appId, setAppId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!appId) {
      alert("Please enter a valid App ID");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.get(`http://127.0.0.1:8000/analyze?app_id=${appId}`);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Error fetching analysis");
    }
    setLoading(false);
  };
// Update handleDownload to download CSV
const handleDownload = async () => {
  if (!appId) return;

  try {
    const res = await axios.get(`http://127.0.0.1:8000/download_csv?app_id=${appId}`, {
      responseType: 'blob', // important to handle file download
    });

    // Create a blob URL
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `cleaned_reviews_${appId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    console.error(err);
    alert("Error downloading CSV");
  }
};

  // Prepare Sentiment Pie Chart Data
  const sentimentData = result
    ? {
        labels: Object.keys(result.sentiment_distribution),
        datasets: [
          {
            label: "Sentiment Distribution",
            data: Object.values(result.sentiment_distribution),
            backgroundColor: ["#66b3ff", "#ff9999", "#99ff99"],
          },
        ],
      }
    : null;

  // Prepare Topic Bar Chart Data
  const topicData = result
    ? {
        labels: Object.keys(result.topic_distribution).map((t) => `Topic ${t}`),
        datasets: [
          {
            label: "Number of Reviews",
            data: Object.values(result.topic_distribution),
            backgroundColor: "#4cafef",
          },
        ],
      }
    : null;

  return (
    <div style={{ maxWidth: "900px", margin: "auto", padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h2 style={{ textAlign: "center", marginBottom: "20px", color: "#333" }}>
        📊 Google Play App Review Analyzer
      </h2>

      <div style={{ display: "flex", justifyContent: "center", marginBottom: "20px" }}>
        <input
          value={appId}
          onChange={(e) => setAppId(e.target.value)}
          placeholder="Enter app ID (e.g. com.ethiopianairlines.ethiopianairlines)"
          style={{
            flex: "1",
            padding: "10px",
            border: "1px solid #ccc",
            borderRadius: "8px",
            marginRight: "10px",
          }}
        />
        <button
          onClick={handleAnalyze}
          style={{
            padding: "10px 20px",
            backgroundColor: "#4cafef",
            border: "none",
            borderRadius: "8px",
            color: "white",
            fontWeight: "bold",
            cursor: "pointer",
            transition: "0.3s",
          }}
          onMouseOver={(e) => (e.target.style.backgroundColor = "#379ed8")}
          onMouseOut={(e) => (e.target.style.backgroundColor = "#4cafef")}
        >
          Analyze
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: "center", marginTop: "30px" }}>
          <div
            style={{
              border: "6px solid #f3f3f3",
              borderTop: "6px solid #4cafef",
              borderRadius: "50%",
              width: "40px",
              height: "40px",
              margin: "auto",
              animation: "spin 1s linear infinite",
            }}
          ></div>
          <p style={{ marginTop: "10px", color: "#555" }}>Analyzing... please wait</p>
          <style>
            {`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}
          </style>
        </div>
      )}

      {result && !loading && (
        <div style={{ marginTop: "30px" }}>
          <h3 style={{ textAlign: "center" }}>Total Reviews: {result.total_reviews}</h3>

          {/* Sentiment Pie Chart */}
          <div style={{ width: "400px", margin: "30px auto" }}>
            <h4 style={{ textAlign: "center" }}>Sentiment Distribution</h4>
            <Pie data={sentimentData} />
          </div>

          {/* Topic Bar Chart */}
          <div style={{ width: "600px", margin: "40px auto" }}>
            <h4 style={{ textAlign: "center" }}>Reviews per Topic</h4>
            <Bar data={topicData} />
          </div>

          {/* Keywords per Topic */}
<div style={{ marginTop: "40px" }}>
  <h4 style={{ textAlign: "center" }}>Top Keywords by Topic</h4>

  {Object.entries(result.topics).map(([topic, phrase]) => (
    <div
      key={topic}
      style={{
        marginBottom: "15px",
        padding: "10px",
        borderRadius: "8px",
        backgroundColor: "#f9f9f9",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
      }}
    >
      <b>{topic}:</b> {phrase}
    </div>
  ))}

  {/* Download button outside the map */}
  <div style={{ display: "flex", justifyContent: "center", marginTop: "20px" }}>
    <button
      style={{ color: "black", padding: "10px 20px", borderRadius: "8px", cursor: "pointer" }}
      onClick={handleDownload}
    >
      Download CSV file
    </button>
  </div>
</div>

        </div>
      )}
    </div>
  );
}

export default App;
