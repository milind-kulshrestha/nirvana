import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Eye, EyeOff, CheckCircle, XCircle, Loader2, Settings as SettingsIcon } from 'lucide-react';
import { API_BASE } from '../config';

const REFRESH_INTERVALS = [
  { value: 5, label: '5 minutes' },
  { value: 10, label: '10 minutes' },
  { value: 15, label: '15 minutes' },
  { value: 30, label: '30 minutes' },
];

export default function Settings() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Form state
  const [anthropicKey, setAnthropicKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [googleKey, setGoogleKey] = useState('');
  const [groqKey, setGroqKey] = useState('');
  const [fmpKey, setFmpKey] = useState('');
  const [defaultModel, setDefaultModel] = useState('anthropic/claude-sonnet-4-6');
  const [availableModels, setAvailableModels] = useState([]);
  const [refreshInterval, setRefreshInterval] = useState(15);
  const [marketHoursOnly, setMarketHoursOnly] = useState(false);

  // Masked values from API (display current status)
  const [maskedAnthropicKey, setMaskedAnthropicKey] = useState('');
  const [maskedOpenaiKey, setMaskedOpenaiKey] = useState('');
  const [maskedGoogleKey, setMaskedGoogleKey] = useState('');
  const [maskedGroqKey, setMaskedGroqKey] = useState('');
  const [maskedFmpKey, setMaskedFmpKey] = useState('');

  // Visibility toggles
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [showGoogleKey, setShowGoogleKey] = useState(false);
  const [showGroqKey, setShowGroqKey] = useState(false);
  const [showFmpKey, setShowFmpKey] = useState(false);

  // Test states: null | 'testing' | 'success' | 'error'
  const [anthropicTestStatus, setAnthropicTestStatus] = useState(null);
  const [fmpTestStatus, setFmpTestStatus] = useState(null);

  useEffect(() => {
    fetchSettings();
    fetch(`${API_BASE}/api/settings/models`, { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : []))
      .then(setAvailableModels)
      .catch(() => {});
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/settings`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setMaskedAnthropicKey(data.anthropic_api_key || '');
        setMaskedOpenaiKey(data.openai_api_key || '');
        setMaskedGoogleKey(data.google_api_key || '');
        setMaskedGroqKey(data.groq_api_key || '');
        setMaskedFmpKey(data.fmp_api_key || '');
        setDefaultModel(data.default_model || 'anthropic/claude-sonnet-4-6');
        setRefreshInterval(data.refresh_interval_minutes ?? 15);
        setMarketHoursOnly(data.market_hours_only ?? false);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const body = {};
      if (anthropicKey && !anthropicKey.includes('*')) body.anthropic_api_key = anthropicKey;
      if (openaiKey && !openaiKey.includes('*')) body.openai_api_key = openaiKey;
      if (googleKey && !googleKey.includes('*')) body.google_api_key = googleKey;
      if (groqKey && !groqKey.includes('*')) body.groq_api_key = groqKey;
      if (fmpKey && !fmpKey.includes('*')) body.fmp_api_key = fmpKey;
      body.default_model = defaultModel;
      body.refresh_interval_minutes = refreshInterval;
      body.market_hours_only = marketHoursOnly;

      const response = await fetch(`${API_BASE}/api/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (response.ok) {
        const data = await response.json();
        setMaskedAnthropicKey(data.anthropic_api_key || '');
        setMaskedOpenaiKey(data.openai_api_key || '');
        setMaskedGoogleKey(data.google_api_key || '');
        setMaskedGroqKey(data.groq_api_key || '');
        setMaskedFmpKey(data.fmp_api_key || '');
        setAnthropicKey('');
        setOpenaiKey('');
        setGoogleKey('');
        setGroqKey('');
        setFmpKey('');
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Error saving settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const testAnthropicKey = async () => {
    setAnthropicTestStatus('testing');
    try {
      // Save key first if user entered a new one
      if (anthropicKey) {
        await fetch(`${API_BASE}/api/settings`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ anthropic_api_key: anthropicKey }),
        });
      }
      const response = await fetch(`${API_BASE}/api/chat/health`, {
        credentials: 'include',
      });
      setAnthropicTestStatus(response.ok ? 'success' : 'error');
    } catch {
      setAnthropicTestStatus('error');
    }
    setTimeout(() => setAnthropicTestStatus(null), 5000);
  };

  const testFmpKey = async () => {
    setFmpTestStatus('testing');
    try {
      // Save key first if user entered a new one
      if (fmpKey) {
        await fetch(`${API_BASE}/api/settings`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ fmp_api_key: fmpKey }),
        });
      }
      const response = await fetch(`${API_BASE}/api/securities/quote/AAPL`, {
        credentials: 'include',
      });
      setFmpTestStatus(response.ok ? 'success' : 'error');
    } catch {
      setFmpTestStatus('error');
    }
    setTimeout(() => setFmpTestStatus(null), 5000);
  };

  const renderTestButton = (status, onTest, label) => {
    if (status === 'testing') {
      return (
        <Button variant="outline" size="sm" disabled>
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          Testing...
        </Button>
      );
    }
    if (status === 'success') {
      return (
        <Badge variant="default" className="bg-green-600 hover:bg-green-600 gap-1">
          <CheckCircle className="h-3 w-3" />
          Valid
        </Badge>
      );
    }
    if (status === 'error') {
      return (
        <Badge variant="destructive" className="gap-1">
          <XCircle className="h-3 w-3" />
          Invalid
        </Badge>
      );
    }
    return (
      <Button variant="outline" size="sm" onClick={onTest}>
        Test
      </Button>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/watchlists')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-3">
            <SettingsIcon className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-2xl space-y-6">
        {/* API Keys Section */}
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>
              Configure your API keys for AI chat and market data.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Anthropic API Key */}
            <div className="space-y-2">
              <Label htmlFor="anthropic-key">Anthropic API Key</Label>
              {maskedAnthropicKey && (
                <p className="text-xs text-muted-foreground">
                  Current: <code className="bg-muted px-1 py-0.5 rounded text-xs">{maskedAnthropicKey}</code>
                </p>
              )}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="anthropic-key"
                    type={showAnthropicKey ? 'text' : 'password'}
                    placeholder="sk-ant-..."
                    value={anthropicKey}
                    onChange={(e) => setAnthropicKey(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showAnthropicKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {renderTestButton(anthropicTestStatus, testAnthropicKey, 'Test')}
              </div>
              <p className="text-xs text-muted-foreground">
                Get your key at{' '}
                <a
                  href="https://console.anthropic.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  console.anthropic.com
                </a>
              </p>
            </div>

            <Separator />

            {/* FMP API Key */}
            <div className="space-y-2">
              <Label htmlFor="fmp-key">FMP API Key</Label>
              {maskedFmpKey && (
                <p className="text-xs text-muted-foreground">
                  Current: <code className="bg-muted px-1 py-0.5 rounded text-xs">{maskedFmpKey}</code>
                </p>
              )}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="fmp-key"
                    type={showFmpKey ? 'text' : 'password'}
                    placeholder="Enter your FMP API key"
                    value={fmpKey}
                    onChange={(e) => setFmpKey(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowFmpKey(!showFmpKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showFmpKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {renderTestButton(fmpTestStatus, testFmpKey, 'Test')}
              </div>
              <p className="text-xs text-muted-foreground">
                Get your key at{' '}
                <a
                  href="https://financialmodelingprep.com/developer"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  financialmodelingprep.com/developer
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Additional AI Providers */}
        <Card>
          <CardHeader>
            <CardTitle>Additional AI Providers</CardTitle>
            <CardDescription>
              Add API keys for other LLM providers to use in the chat sidebar.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Default Model */}
            <div className="space-y-2">
              <Label htmlFor="default-model">Default Model</Label>
              <select
                id="default-model"
                value={defaultModel}
                onChange={(e) => setDefaultModel(e.target.value)}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                {availableModels.map((m) => (
                  <option key={m.id} value={m.id}>{m.display_name} ({m.provider})</option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">Model used for new conversations.</p>
            </div>

            <Separator />

            {/* OpenAI API Key */}
            <div className="space-y-2">
              <Label htmlFor="openai-key">OpenAI API Key</Label>
              {maskedOpenaiKey && (
                <p className="text-xs text-muted-foreground">
                  Current: <code className="bg-muted px-1 py-0.5 rounded text-xs">{maskedOpenaiKey}</code>
                </p>
              )}
              <div className="relative">
                <Input
                  id="openai-key"
                  type={showOpenaiKey ? 'text' : 'password'}
                  placeholder="sk-..."
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showOpenaiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Separator />

            {/* Google API Key */}
            <div className="space-y-2">
              <Label htmlFor="google-key">Google AI API Key</Label>
              {maskedGoogleKey && (
                <p className="text-xs text-muted-foreground">
                  Current: <code className="bg-muted px-1 py-0.5 rounded text-xs">{maskedGoogleKey}</code>
                </p>
              )}
              <div className="relative">
                <Input
                  id="google-key"
                  type={showGoogleKey ? 'text' : 'password'}
                  placeholder="AIza..."
                  value={googleKey}
                  onChange={(e) => setGoogleKey(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowGoogleKey(!showGoogleKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showGoogleKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Separator />

            {/* Groq API Key */}
            <div className="space-y-2">
              <Label htmlFor="groq-key">Groq API Key</Label>
              {maskedGroqKey && (
                <p className="text-xs text-muted-foreground">
                  Current: <code className="bg-muted px-1 py-0.5 rounded text-xs">{maskedGroqKey}</code>
                </p>
              )}
              <div className="relative">
                <Input
                  id="groq-key"
                  type={showGroqKey ? 'text' : 'password'}
                  placeholder="gsk_..."
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowGroqKey(!showGroqKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showGroqKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Section */}
        <Card>
          <CardHeader>
            <CardTitle>Data</CardTitle>
            <CardDescription>
              Configure how market data is fetched and refreshed.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Refresh Interval */}
            <div className="space-y-2">
              <Label htmlFor="refresh-interval">Refresh Interval</Label>
              <select
                id="refresh-interval"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                {REFRESH_INTERVALS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                How often to automatically refresh stock data.
              </p>
            </div>

            <Separator />

            {/* Market Hours Only */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="market-hours">Market Hours Only</Label>
                <p className="text-xs text-muted-foreground">
                  Only fetch live data during market hours (9:30 AM - 4:00 PM ET).
                </p>
              </div>
              <Switch
                id="market-hours"
                checked={marketHoursOnly}
                onCheckedChange={setMarketHoursOnly}
              />
            </div>
          </CardContent>
        </Card>

        {/* About Section */}
        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Version</span>
              <Badge variant="secondary">0.1.0</Badge>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Application</span>
              <span className="text-sm font-medium">Nirvana</span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Market Data</span>
              <span className="text-sm">
                <a
                  href="https://financialmodelingprep.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Financial Modeling Prep
                </a>
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">AI Assistant</span>
              <span className="text-sm">
                <a
                  href="https://anthropic.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  Anthropic Claude
                </a>
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex items-center justify-end gap-3">
          {saved && (
            <span className="text-sm text-green-600 flex items-center gap-1">
              <CheckCircle className="h-4 w-4" />
              Settings saved
            </span>
          )}
          <Button onClick={handleSave} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </Button>
        </div>
      </main>
    </div>
  );
}
