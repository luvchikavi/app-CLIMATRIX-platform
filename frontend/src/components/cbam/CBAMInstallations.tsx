'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableEmpty,
} from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { ConfirmDialog, toast } from '@/components/ui';
import { api } from '@/lib/api';
import type { CBAMInstallation, CBAMInstallationCreate, CBAMSector } from '@/lib/types';
import { Plus, Factory, Trash2, Edit, X, Check, Globe } from 'lucide-react';

const CBAM_SECTORS: { value: CBAMSector; label: string }[] = [
  { value: 'cement', label: 'Cement' },
  { value: 'iron_steel', label: 'Iron & Steel' },
  { value: 'aluminium', label: 'Aluminium' },
  { value: 'fertilisers', label: 'Fertilisers' },
  { value: 'electricity', label: 'Electricity' },
  { value: 'hydrogen', label: 'Hydrogen' },
];

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  verified: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  expired: 'bg-gray-100 text-gray-700',
};

export function CBAMInstallations() {
  const [installations, setInstallations] = useState<CBAMInstallation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<CBAMInstallationCreate>({
    name: '',
    country_code: '',
    address: '',
    contact_name: '',
    contact_email: '',
    sectors: [],
  });
  const [saving, setSaving] = useState(false);
  const [confirmState, setConfirmState] = useState<{open: boolean; onConfirm: () => void; title: string; message: string}>({open: false, onConfirm: () => {}, title: '', message: ''});

  useEffect(() => {
    loadInstallations();
  }, []);

  const loadInstallations = async () => {
    try {
      setLoading(true);
      const data = await api.getCBAMInstallations();
      setInstallations(data);
    } catch (err) {
      console.error('Failed to load installations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.country_code) return;

    try {
      setSaving(true);
      if (editingId) {
        await api.updateCBAMInstallation(editingId, formData);
      } else {
        await api.createCBAMInstallation(formData);
      }
      await loadInstallations();
      resetForm();
    } catch (err) {
      console.error('Failed to save installation:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (installation: CBAMInstallation) => {
    setEditingId(installation.id);
    setFormData({
      name: installation.name,
      country_code: installation.country_code,
      address: installation.address || '',
      contact_name: installation.contact_name || '',
      contact_email: installation.contact_email || '',
      sectors: installation.sectors,
    });
    setShowForm(true);
  };

  const handleDelete = (id: string) => {
    setConfirmState({
      open: true,
      onConfirm: async () => {
        setConfirmState(s => ({...s, open: false}));
        try {
          await api.deleteCBAMInstallation(id);
          await loadInstallations();
        } catch (err) {
          console.error('Failed to delete installation:', err);
          toast.error('Cannot delete installation with linked imports');
        }
      },
      title: 'Delete Installation',
      message: 'Are you sure you want to delete this installation?',
    });
  };

  const resetForm = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData({
      name: '',
      country_code: '',
      address: '',
      contact_name: '',
      contact_email: '',
      sectors: [],
    });
  };

  const toggleSector = (sector: CBAMSector) => {
    setFormData((prev) => ({
      ...prev,
      sectors: prev.sectors?.includes(sector)
        ? prev.sectors.filter((s) => s !== sector)
        : [...(prev.sectors || []), sector],
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">CBAM Installations</h2>
          <p className="text-foreground-muted">Manage non-EU production facilities for CBAM reporting</p>
        </div>
        <Button onClick={() => setShowForm(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Installation
        </Button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Edit Installation' : 'Add New Installation'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Installation Name *"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Steel Works Factory"
                  required
                />
                <Input
                  label="Country Code *"
                  value={formData.country_code}
                  onChange={(e) => setFormData({ ...formData, country_code: e.target.value.toUpperCase() })}
                  placeholder="e.g., CN, IN, TR"
                  maxLength={2}
                  required
                />
                <Input
                  label="Address"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Full address"
                />
                <Input
                  label="Contact Name"
                  value={formData.contact_name}
                  onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                  placeholder="Contact person"
                />
                <Input
                  label="Contact Email"
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  placeholder="email@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Sectors</label>
                <div className="flex flex-wrap gap-2">
                  {CBAM_SECTORS.map((sector) => (
                    <button
                      key={sector.value}
                      type="button"
                      onClick={() => toggleSector(sector.value)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        formData.sectors?.includes(sector.value)
                          ? 'bg-primary text-white'
                          : 'bg-background-muted text-foreground hover:bg-background-muted/80'
                      }`}
                    >
                      {sector.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button type="button" variant="ghost" onClick={resetForm}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={saving}>
                  {editingId ? 'Update' : 'Create'} Installation
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Installations Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Country</TableHead>
              <TableHead>Sectors</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead className="w-24">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </TableCell>
              </TableRow>
            ) : installations.length === 0 ? (
              <TableEmpty
                colSpan={6}
                icon={<Factory className="w-12 h-12" />}
                title="No installations yet"
                description="Add your first non-EU production facility to start tracking CBAM imports"
                action={
                  <Button size="sm" onClick={() => setShowForm(true)}>
                    Add Installation
                  </Button>
                }
              />
            ) : (
              installations.map((inst) => (
                <TableRow key={inst.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Factory className="w-4 h-4 text-foreground-muted" />
                      <span className="font-medium">{inst.name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Globe className="w-4 h-4 text-foreground-muted" />
                      {inst.country_code}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {inst.sectors.map((sector) => (
                        <Badge key={sector} variant="secondary" size="sm">
                          {sector.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[inst.verification_status]}`}>
                      {inst.verification_status}
                    </span>
                  </TableCell>
                  <TableCell>
                    {inst.contact_name && (
                      <div className="text-sm">
                        <p>{inst.contact_name}</p>
                        <p className="text-foreground-muted">{inst.contact_email}</p>
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(inst)}>
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(inst.id)}>
                        <Trash2 className="w-4 h-4 text-error" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
      <ConfirmDialog
        isOpen={confirmState.open}
        onClose={() => setConfirmState(s => ({...s, open: false}))}
        onConfirm={confirmState.onConfirm}
        title={confirmState.title}
        message={confirmState.message}
        variant="danger"
        confirmLabel="Delete"
      />
    </div>
  );
}
