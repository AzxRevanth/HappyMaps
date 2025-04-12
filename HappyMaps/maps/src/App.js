import React, { useEffect } from 'react';
import './App.css';

let latitudes = [];
let longitudes = [];
let happinessScores = [];
let map, heatmap;

const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;


function App() {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=visualization`;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      initMap();
    };
    document.head.appendChild(script);
  }, []);

  function getEmojiUrl(score) {
    if (score >= 6) {
      return "/emoji/super-happy.png";
    } else if (score >= 5) {
      return "/emoji/happy.png";
    } else if (score >= 4) {
      return "/emoji/neutral.png";
    } else if (score >= 2) {
      return "/emoji/sad.png";
    } else {
      return "/emoji/super-sad.png";
    }
  }

  function initMap() {
    fetch("http://localhost:5000/api/emotion")
      .then(response => response.json())
      .then(data => {
        data.forEach(row => {
          latitudes.push(parseFloat(row.latitude));
          longitudes.push(parseFloat(row.longitude));
          happinessScores.push(parseFloat(row.score));
        });

        map = new window.google.maps.Map(document.getElementById("map"), {
          zoom: 5.3,
          center: { lat: 22.9734, lng: 78.6569 },
          mapTypeId: "satellite",
        });

        const gradient = [
          "rgba(0, 255, 255, 0)",
          "rgba(0, 255, 255, 1)",
          "rgba(0, 191, 255, 1)",
          "rgba(0, 127, 255, 1)",
          "rgba(0, 63, 255, 1)",
          "rgba(0, 0, 255, 1)",
          "rgba(0, 0, 223, 1)",
          "rgba(0, 0, 191, 1)",
          "rgba(0, 0, 159, 1)",
          "rgba(0, 0, 127, 1)",
          "rgba(63, 0, 91, 1)",
          "rgba(127, 0, 63, 1)",
          "rgba(191, 0, 31, 1)",
          "rgba(255, 0, 0, 1)",
        ];

        heatmap = new window.google.maps.visualization.HeatmapLayer({
          data: getPoints(),
          map: map,
          gradient: gradient, 
          radius: 30,
        });
        

    latitudes.forEach((lat, index) => {
      const marker = new window.google.maps.Marker({
        position: { lat: lat, lng: longitudes[index] },
        map: map,
        title: `Happiness Score: ${happinessScores[index]}`,
        icon: {
          url: getEmojiUrl(happinessScores[index]),
          scaledSize: new window.google.maps.Size(30, 30),
        },
      });
    });

        document
          .getElementById("toggle-heatmap")
          .addEventListener("click", toggleHeatmap);
        document
          .getElementById("change-opacity")
          .addEventListener("click", changeOpacity);
        document
          .getElementById("change-radius")
          .addEventListener("click", changeRadius);
      });
  }

  function toggleHeatmap() {
    heatmap.setMap(heatmap.getMap() ? null : map);
  }

  function changeRadius() {
    heatmap.set("radius", heatmap.get("radius") ? null : 40);
  }

  function changeOpacity() {
    heatmap.set("opacity", heatmap.get("opacity") ? null : 0.2);
  }

  function getPoints() {
    return latitudes.map((lat, index) => {
      return {
        location: new window.google.maps.LatLng(lat, longitudes[index]),
        weight: happinessScores[index],
      };
    });
  }

  return (
    <div className="landing-page">
      <div className="content">
        <h1 className="title">Happy Maps</h1>
        <p className="subtitle">Tagline</p>
      </div>

      <div className='Map'>
        <div id='floating-panel'>
          <button id="toggle-heatmap">Toggle Heatmap</button>
          <button id="change-radius">Change radius</button>
          <button id="change-opacity">Change opacity</button>
        </div>

        <div id="map" style={{ height: '500px', width: '100%' }}></div>
      </div>
    </div>
  );
}

export default App;
