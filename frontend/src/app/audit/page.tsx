'use client';

import { useState, useEffect, Suspense } from 'react';
import { useAuthStore } from '@/stores/auth';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api, AuditLogEntry, AuditAction } from '@/lib/api';
import { AppShell } from '@/components/layout';
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  EmptyState,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  History,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Filter,
  Download,
  User,
  Calendar,
  Activity,
  FileText,
  LogIn,
  LogOut,
  Upload,
  Trash2,
  Edit,
  UserPlus,
  Shield,
  RefreshCw,
} from 'lucide-react';

function AuditPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuthStore();

  const [mounted, setMounted] = useState(false);
  const [page, setPage] = useState(0);
  const [actionFilter, setActionFilter] = useState<AuditAction | ''>('');
  const [resourceFilter, setResourceFilter] = useState('');
  const limit = 25;

  // Fetch audit logs
  const { data: auditLogs, isLoading } = useQuery({
    queryKey: ['audit-logs', page, actionFilter, resourceFilter],
    queryFn: () =>
      api.getAuditLogs({
        limit,
        offset: page * limit,
        action: actionFilter || undefined,
        resource_type: resourceFilter || undefined,
      }),
    enabled: isAuthenticated && (user?.role === 'admin' || user?.role === 'super_admin'),
  });

  // Fetch audit stats
  const { data: auditStats } = useQuery({
    queryKey: ['audit-stats'],
    queryFn: () => api.getAuditStats(),
    enabled: isAuthenticated && (user?.role === 'admin' || user?.role === 'super_admin'),
  });

  // Fetch available resource types
  const { data: resourceTypes } = useQuery({
    queryKey: ['audit-resource-types'],
    queryFn: () => api.getAuditResourceTypes(),
    enabled: isAuthenticated && (user?.role === 'admin' || user?.role === 'super_admin'),
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push('/');
    }
  }, [mounted, isAuthenticated, router]);

  // Check admin access
  useEffect(() => {
    if (mounted && isAuthenticated && user?.role !== 'admin' && user?.role !== 'super_admin') {
      router.push('/dashboard');
    }
  }, [mounted, isAuthenticated, user, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'create':
        return Activity;
      case 'update':
        return Edit;
      case 'delete':
        return Trash2;
      case 'login':
        return LogIn;
      case 'logout':
        return LogOut;
      case 'import':
        return Upload;
      case 'export':
        return Download;
      case 'status_change':
        return RefreshCw;
      case 'invite':
        return UserPlus;
      case 'permission_change':
        return Shield;
      default:
        return Activity;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'create':
        return 'bg-success/10 text-success';
      case 'update':
        return 'bg-primary/10 text-primary';
      case 'delete':
        return 'bg-error/10 text-error';
      case 'login':
        return 'bg-secondary/10 text-secondary';
      case 'logout':
        return 'bg-foreground-muted/10 text-foreground-muted';
      case 'import':
        return 'bg-primary/10 text-primary';
      case 'export':
        return 'bg-warning/10 text-warning';
      case 'invite':
        return 'bg-success/10 text-success';
      default:
        return 'bg-foreground-muted/10 text-foreground-muted';
    }
  };

  const totalPages = auditLogs ? Math.ceil(auditLogs.total / limit) : 0;

  return (
    <AppShell>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Audit Trail</h1>
          <p className="text-foreground-muted mt-1">
            Track all actions and changes in your organization
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      {auditStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <History className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{auditStats.total_events.toLocaleString()}</p>
                <p className="text-sm text-foreground-muted">Total Events</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/10">
                <Activity className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{auditStats.recent_activity_count}</p>
                <p className="text-sm text-foreground-muted">Last 24 Hours</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-secondary/10">
                <FileText className="w-5 h-5 text-secondary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{Object.keys(auditStats.events_by_resource).length}</p>
                <p className="text-sm text-foreground-muted">Resource Types</p>
              </div>
            </div>
          </Card>
          <Card padding="md">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-warning/10">
                <Filter className="w-5 h-5 text-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">{Object.keys(auditStats.events_by_action).length}</p>
                <p className="text-sm text-foreground-muted">Action Types</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card padding="md" className="mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-foreground-muted mb-1">Action Type</label>
            <select
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value as AuditAction | '');
                setPage(0);
              }}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
            >
              <option value="">All Actions</option>
              <option value="create">Create</option>
              <option value="update">Update</option>
              <option value="delete">Delete</option>
              <option value="login">Login</option>
              <option value="import">Import</option>
              <option value="export">Export</option>
              <option value="status_change">Status Change</option>
              <option value="invite">Invite</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-foreground-muted mb-1">Resource Type</label>
            <select
              value={resourceFilter}
              onChange={(e) => {
                setResourceFilter(e.target.value);
                setPage(0);
              }}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
            >
              <option value="">All Resources</option>
              {resourceTypes?.resource_types.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <Button
              variant="outline"
              onClick={() => {
                setActionFilter('');
                setResourceFilter('');
                setPage(0);
              }}
            >
              Clear Filters
            </Button>
          </div>
        </div>
      </Card>

      {/* Audit Log List */}
      <Card padding="none">
        <CardHeader className="p-4 border-b border-border">
          <CardTitle className="flex items-center gap-2">
            <History className="w-5 h-5 text-foreground-muted" />
            Activity Log
            {auditLogs && (
              <Badge variant="secondary" className="ml-2">
                {auditLogs.total.toLocaleString()} entries
              </Badge>
            )}
          </CardTitle>
        </CardHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        )}

        {!isLoading && (!auditLogs || auditLogs.items.length === 0) && (
          <div className="p-8">
            <EmptyState
              variant="minimal"
              title="No audit logs found"
              description={
                actionFilter || resourceFilter
                  ? 'Try adjusting your filters to see more results.'
                  : 'Activity will appear here as users interact with the system.'
              }
            />
          </div>
        )}

        {!isLoading && auditLogs && auditLogs.items.length > 0 && (
          <>
            <div className="divide-y divide-border">
              {auditLogs.items.map((log) => {
                const Icon = getActionIcon(log.action);
                const colorClass = getActionColor(log.action);

                return (
                  <div key={log.id} className="p-4 hover:bg-background-muted transition-colors">
                    <div className="flex items-start gap-4">
                      <div className={cn('p-2 rounded-lg', colorClass)}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground">{log.description}</p>
                        <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-foreground-muted">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {log.user_email || 'System'}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(log.created_at).toLocaleString()}
                          </span>
                          <Badge variant="secondary" className="text-xs">
                            {log.resource_type}
                          </Badge>
                        </div>
                      </div>
                      <Badge variant="secondary" className="capitalize">
                        {log.action.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between p-4 border-t border-border">
              <p className="text-sm text-foreground-muted">
                Showing {page * limit + 1} to {Math.min((page + 1) * limit, auditLogs.total)} of {auditLogs.total}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 0}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                <span className="text-sm text-foreground-muted px-2">
                  Page {page + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages - 1}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </AppShell>
  );
}

function AuditLoading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-primary animate-spin" />
    </div>
  );
}

export default function AuditPage() {
  return (
    <Suspense fallback={<AuditLoading />}>
      <AuditPageContent />
    </Suspense>
  );
}
