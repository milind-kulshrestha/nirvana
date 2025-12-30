import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import PriceChart from './PriceChart';
import ValuationChart from './ValuationChart';

const API_BASE = 'http://localhost:8000';

export default function StockAnalytics({ symbol }) {
  const [activeTab, setActiveTab] = useState('price');
  const [priceData, setPriceData] = useState(null);
  const [ratiosData, setRatiosData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [priceRes, ratiosRes] = await Promise.all([
          fetch(`${API_BASE}/api/securities/${symbol}?include=history`, {
            credentials: 'include',
          }),
          fetch(`${API_BASE}/api/securities/${symbol}/ratios`, {
            credentials: 'include',
          })
        ]);

        if (priceRes.ok) {
          const data = await priceRes.json();
          setPriceData(data.history || []);
        }

        if (ratiosRes.ok) {
          const data = await ratiosRes.json();
          setRatiosData(data);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol]);

  if (loading) {
    return (
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <div className="text-center text-gray-500 py-8">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-50 border-t border-gray-200 p-4">
        <div className="text-center text-red-600 py-8">Error loading data: {error}</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 border-t border-gray-200 p-4">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="price">Price History</TabsTrigger>
          <TabsTrigger value="valuation">Valuation Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="price" className="mt-0">
          {priceData && priceData.length > 0 ? (
            <div className="bg-white rounded-lg p-4">
              <PriceChart symbol={symbol} data={priceData} />
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">No price data available</div>
          )}
        </TabsContent>

        <TabsContent value="valuation" className="mt-0">
          {ratiosData && ratiosData.length > 0 ? (
            <div className="bg-white rounded-lg">
              <ValuationChart data={ratiosData} />
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">No valuation data available</div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
