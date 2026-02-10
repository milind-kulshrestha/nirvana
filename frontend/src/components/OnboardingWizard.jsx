import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, CheckCircle, ArrowRight, Sparkles } from 'lucide-react';
import { API_BASE } from '../config';

const STEPS = [
  {
    key: 'anthropic_api_key',
    title: 'Anthropic API Key',
    description: 'Power the AI assistant with Claude. This key enables conversational analysis of your watchlists.',
    placeholder: 'sk-ant-...',
    linkText: 'Get your key at console.anthropic.com',
    linkUrl: 'https://console.anthropic.com',
  },
  {
    key: 'fmp_api_key',
    title: 'FMP API Key',
    description: 'Financial Modeling Prep provides real-time stock quotes, historical data, and financial metrics.',
    placeholder: 'Enter your FMP API key',
    linkText: 'Get your key at financialmodelingprep.com/developer',
    linkUrl: 'https://financialmodelingprep.com/developer',
  },
];

export default function OnboardingWizard({ missingKeys, onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [keyValue, setKeyValue] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [completedSteps, setCompletedSteps] = useState([]);

  // Filter steps to only show missing ones
  const activeSteps = STEPS.filter((s) => missingKeys.includes(s.key));
  const totalSteps = activeSteps.length + 1; // +1 for confirmation step
  const isLastKeyStep = currentStep >= activeSteps.length;
  const step = activeSteps[currentStep];

  const saveKey = async () => {
    if (!keyValue.trim()) return;
    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ [step.key]: keyValue }),
      });
      if (response.ok) {
        setCompletedSteps([...completedSteps, step.key]);
        setKeyValue('');
        setShowKey(false);
        setCurrentStep(currentStep + 1);
      }
    } catch (error) {
      console.error('Error saving key:', error);
    } finally {
      setSaving(false);
    }
  };

  const skipStep = () => {
    setKeyValue('');
    setShowKey(false);
    setCurrentStep(currentStep + 1);
  };

  // Confirmation step (final)
  if (isLastKeyStep) {
    return (
      <div className="fixed inset-0 z-[100] bg-background/95 backdrop-blur-sm flex items-center justify-center p-4">
        <Card className="w-full max-w-lg shadow-2xl">
          <CardHeader className="text-center pb-2">
            {/* Step indicator */}
            <div className="flex items-center justify-center gap-2 mb-6">
              {Array.from({ length: totalSteps }).map((_, i) => (
                <div
                  key={i}
                  className={`h-2 rounded-full transition-all ${
                    i <= currentStep ? 'bg-primary w-8' : 'bg-muted w-8'
                  }`}
                />
              ))}
            </div>
            <div className="flex justify-center mb-4">
              <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <CardTitle className="text-2xl">You're All Set!</CardTitle>
            <CardDescription className="text-base mt-2">
              {completedSteps.length === activeSteps.length
                ? 'All API keys have been configured. You can update them anytime in Settings.'
                : 'You can configure any remaining keys later in Settings.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <Button className="w-full" size="lg" onClick={onComplete}>
              <Sparkles className="mr-2 h-5 w-5" />
              Get Started
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[100] bg-background/95 backdrop-blur-sm flex items-center justify-center p-4">
      <Card className="w-full max-w-lg shadow-2xl">
        <CardHeader className="pb-2">
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {Array.from({ length: totalSteps }).map((_, i) => (
              <div
                key={i}
                className={`h-2 rounded-full transition-all ${
                  i <= currentStep ? 'bg-primary w-8' : 'bg-muted w-8'
                }`}
              />
            ))}
          </div>
          <div className="text-sm text-muted-foreground text-center mb-2">
            Step {currentStep + 1} of {totalSteps}
          </div>
          <CardTitle className="text-2xl text-center">{step.title}</CardTitle>
          <CardDescription className="text-center text-base mt-2">
            {step.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="onboarding-key">API Key</Label>
            <div className="relative">
              <Input
                id="onboarding-key"
                type={showKey ? 'text' : 'password'}
                placeholder={step.placeholder}
                value={keyValue}
                onChange={(e) => setKeyValue(e.target.value)}
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && keyValue.trim()) {
                    saveKey();
                  }
                }}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              <a
                href={step.linkUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {step.linkText}
              </a>
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={skipStep}
            >
              Skip for now
            </Button>
            <Button
              className="flex-1"
              onClick={saveKey}
              disabled={!keyValue.trim() || saving}
            >
              {saving ? 'Saving...' : (
                <>
                  Continue
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
