'use client';
import { useEffect, useState } from "react";

export default function Home() {
  const [minTemp, setMinTemp] = useState("");
  const [avgTemp, setAvgTemp] = useState("");
  const [maxTemp, setMaxTemp] = useState("");

  const [minEnergy, setMinEnergy] = useState("");
  const [avgEnergy, setAvgEnergy] = useState("");
  const [maxEnergy, setMaxEnergy] = useState("");

  const [minHumidity, setMinHumidity] = useState("");
  const [avgHumidity, setAvgHumidity] = useState("");
  const [maxHumidity, setMaxHumidity] = useState("");
  
  const [alerts, setAlerts] = useState("");

  useEffect(() => {
    const fetchData = async () => {

      const query = `
          query {
            temp: aggregatedReadings(type: "temperature") {
              minValue
              maxValue
              avgValue
            }
            energy: aggregatedReadings(type: "energy") {
              minValue
              maxValue
              avgValue
            }
            humidity: aggregatedReadings(type: "humidity") {
              minValue
              maxValue
              avgValue
            }
            alertCount {
              count
            }
          }
      `;

      try {
        const response = await fetch("http://localhost:8000/graphql", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ query })
        });

        const result = await response.json();

        if (result.data) {
          const { temp, energy, humidity, alertCount } = result.data;
          const t = temp[0] || {};
          const e = energy[0] || {};
          const h = humidity[0] || {};

          setMinTemp(typeof t.minValue === "number" ? t.minValue.toFixed(2) : "");
          setAvgTemp(typeof t.avgValue === "number" ? t.avgValue.toFixed(2) : "");
          setMaxTemp(typeof t.maxValue === "number" ? t.maxValue.toFixed(2) : "");

          setMinEnergy(typeof e.minValue === "number" ? e.minValue.toFixed(2) : "");
          setAvgEnergy(typeof e.avgValue === "number" ? e.avgValue.toFixed(2) : "");
          setMaxEnergy(typeof e.maxValue === "number" ? e.maxValue.toFixed(2) : "");

          setMinHumidity(typeof h.minValue === "number" ? h.minValue.toFixed(2) : "");
          setAvgHumidity(typeof h.avgValue === "number" ? h.avgValue.toFixed(2) : "");
          setMaxHumidity(typeof h.maxValue === "number" ? h.maxValue.toFixed(2) : "");

          setAlerts(alertCount.count)

        }
      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    fetchData();
  }, []);




  return (
    <div className="text-black flex flex-row w-screen justify-center ">
      <div className="container flex flex-wrap  gap-5 mt-10">
        <div className="text-3xl w-full text-center">
          The dashboard
        </div>
        {/* Temperature stuff */}
        <div className="w-100 flex flex-col shadow-md bg-white rounded-md p-5 hover:shadow-xl">
          <div className="text-xl w-full text-center">
            Temperature
          </div>
          <div className="mt-3 flex flex-row justify-between">
            <div className="flex flex-col gap-2">
              <div className="text-md">
                min
              </div>
              <div>
                {minTemp}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="text-md">
                Average
              </div>
              <div>
                {avgTemp}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="text-md">
                max
              </div>
              <div>
                {maxTemp}
              </div>
            </div>

          </div>
        </div>
        
        {/* Humidity stuff */}
        <div className="w-100 flex flex-col shadow-md bg-white rounded-md p-5 hover:shadow-xl">
          <div className="text-xl w-full text-center">
            Humidity
          </div>
          <div className="mt-3 flex flex-row justify-between">
            <div className="flex flex-col gap-2">
              <div className="text-md">
                min
              </div>
              <div>
                {minHumidity}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="text-md">
                Average
              </div>
              <div>
                {avgHumidity}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="text-md">
                max
              </div>
              <div>
                {maxHumidity}
              </div>
            </div>

          </div>
        </div>
        
        {/* Energh stuff */}
        <div className="w-100 flex flex-col shadow-md bg-white rounded-md p-5 hover:shadow-xl">
          <div className="text-xl w-full text-center">
            Energy
          </div>
          <div className="mt-3 flex flex-row justify-between">
            <div className="flex flex-col gap-2">
              <div className="text-md">
                min
              </div>
              <div>
                {minEnergy}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="text-md">
                Average
              </div>
              <div>
                {avgEnergy}
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="text-md">
                max
              </div>
              <div>
                {maxEnergy}
              </div>
            </div>

          </div>
        </div>
        
        {/* Alert stuff */}
        <div className="w-100 flex flex-col shadow-md bg-white rounded-md p-5 hover:shadow-xl">
          <div className="text-xl w-full text-center">
            Alerts
          </div>
         <div className="text-red-500 text-center w-full">
            {alerts}
         </div>
        </div>

      </div>

    </div>
  );
}