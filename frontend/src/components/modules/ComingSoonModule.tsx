'use client';

import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout';
import { Card, CardContent, Button, Badge, Input } from '@/components/ui';
import { cn } from '@/lib/utils';
import { ArrowLeft, Bell, Mail, ExternalLink } from 'lucide-react';
import { useState } from 'react';

interface ComingSoonModuleProps {
  name: string;
  description: string;
  icon: React.ElementType;
  color: string;
  features: string[];
  expectedDate?: string;
}

export function ComingSoonModule({
  name,
  description,
  icon: Icon,
  color,
  features,
  expectedDate,
}: ComingSoonModuleProps) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = () => {
    if (email) {
      setSubscribed(true);
      // In production, this would call an API to subscribe the user
    }
  };

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/modules')}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Modules
        </Button>
        <div className="flex items-center gap-3">
          <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', color)}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{name}</h1>
            <p className="text-foreground-muted">{description}</p>
          </div>
        </div>
        <Badge variant="secondary" className="ml-auto">Coming Soon</Badge>
      </div>

      {/* Coming Soon Content */}
      <div className="max-w-2xl mx-auto">
        <Card padding="lg" className="text-center mb-8">
          <CardContent>
            <div className={cn('w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6', color)}>
              <Icon className="w-10 h-10 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-foreground mb-4">
              {name} is Coming Soon
            </h2>

            <p className="text-foreground-muted mb-6 max-w-md mx-auto">
              We're working hard to bring you this powerful module.
              {expectedDate && ` Expected release: ${expectedDate}.`}
            </p>

            {/* Features Preview */}
            <div className="bg-background-muted rounded-xl p-6 mb-6 text-left">
              <h3 className="font-semibold text-foreground mb-4">What to Expect</h3>
              <ul className="space-y-3">
                {features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <div className={cn('w-2 h-2 rounded-full', color)} />
                    <span className="text-foreground-muted">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Newsletter Signup */}
            {!subscribed ? (
              <div className="bg-primary-light rounded-xl p-6">
                <div className="flex items-center justify-center gap-2 mb-4">
                  <Bell className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-foreground">Get Notified</h3>
                </div>
                <p className="text-sm text-foreground-muted mb-4">
                  Be the first to know when {name} launches. Enter your email below.
                </p>
                <div className="flex gap-2 max-w-sm mx-auto">
                  <Input
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    variant="primary"
                    onClick={handleSubscribe}
                    disabled={!email}
                  >
                    Notify Me
                  </Button>
                </div>
              </div>
            ) : (
              <div className="bg-success/10 rounded-xl p-6">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <Mail className="w-5 h-5 text-success" />
                  <h3 className="font-semibold text-success">You're on the list!</h3>
                </div>
                <p className="text-sm text-foreground-muted">
                  We'll notify you at {email} when {name} launches.
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Contact Sales */}
        <Card padding="lg" className="text-center">
          <CardContent>
            <h3 className="font-semibold text-foreground mb-2">Need it sooner?</h3>
            <p className="text-sm text-foreground-muted mb-4">
              Contact our sales team to discuss early access or custom implementation.
            </p>
            <Button
              variant="outline"
              rightIcon={<ExternalLink className="w-4 h-4" />}
            >
              Contact Sales
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
