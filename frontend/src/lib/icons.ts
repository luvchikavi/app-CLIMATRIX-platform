/**
 * CLIMATRIX Icon System
 *
 * Centralized icon exports using Lucide React
 * NO EMOJIS - only professional icons
 */

export {
  // Navigation & Layout
  Menu,
  X,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Home,
  Settings,
  LogOut,
  User,
  Users,
  Bell,
  Search,
  MoreHorizontal,
  MoreVertical,
  ExternalLink,
  Link,
  Copy,
  Maximize2,
  Minimize2,
  SidebarOpen,
  SidebarClose,
  PanelLeft,
  PanelRight,

  // Actions
  Plus,
  Minus,
  Check,
  X as Close,
  Edit,
  Edit2,
  Edit3,
  Trash,
  Trash2,
  Save,
  Download,
  Upload,
  RefreshCw,
  RotateCcw,
  Filter,
  SortAsc,
  SortDesc,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  Archive,
  Unlink,

  // Data & Analytics
  BarChart,
  BarChart2,
  BarChart3,
  LineChart,
  PieChart,
  Activity,
  TrendingUp,
  TrendingDown,
  Percent,
  Calculator,
  Database,
  Table,
  Grid,
  Layers,
  Target,
  Gauge,

  // GHG Scope Icons
  Flame, // Scope 1 - Direct combustion
  Zap, // Scope 2 - Electricity
  Factory, // Scope 1 - Industrial
  Car, // Scope 1 - Mobile
  Truck, // Scope 3 - Transport
  Plane, // Scope 3 - Business travel
  Building, // Organization
  Building2, // Sites/Facilities
  MapPin, // Locations
  Globe, // Global/International

  // Category Icons
  Fuel, // Stationary combustion
  Droplet, // Liquid fuels
  Wind, // Fugitive emissions
  Thermometer, // Refrigerants
  Snowflake, // Cooling
  Sun, // Heat
  Leaf, // Sustainability
  TreePine, // Carbon offsets
  Recycle, // Waste recycling
  Trash as Waste, // Waste disposal
  Package, // Purchased goods
  ShoppingCart, // Procurement
  Train, // Rail transport
  Ship, // Maritime transport
  Bike, // Low-carbon transport
  CircleDot, // Other activities

  // Documents & Files
  File,
  FileText,
  FileSpreadsheet,
  FilePlus,
  FileCheck,
  FileWarning,
  FileX,
  Folder,
  FolderOpen,
  FolderPlus,
  Paperclip,
  Image,
  FileDown,
  FileUp,

  // Reports & Output
  ClipboardList,
  ClipboardCheck,
  BookOpen,
  FileOutput,
  Printer,
  Share2,
  Send,
  Mail,

  // Status & Feedback
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  CheckCircle2,
  XCircle,
  Info,
  HelpCircle,
  Clock,
  Calendar,
  CalendarDays,
  Timer,
  Hourglass,
  Loader,
  Loader2,
  CircleSlash,

  // Forms & Input
  Pencil,
  PenTool,
  Type,
  Hash,
  AtSign,
  List,
  ListChecks,
  ListOrdered,
  ListFilter,
  ToggleLeft,
  ToggleRight,
  Circle,
  Square,
  CheckSquare,

  // AI & Smart Features
  Sparkles,
  Wand2,
  Brain,
  Lightbulb,
  Cpu,
  Bot,
  Workflow,
  GitBranch,

  // Modules (Future Features)
  Coins, // PCAF - Financial
  Scale, // CBAM - Trade compliance
  Microscope, // LCA - Life cycle
  FileStack, // EPD - Environmental declarations
  BadgeCheck, // Certification
  Award, // Achievements
  ShieldCheck, // Compliance
  ScrollText, // Regulatory

  // Misc Utility
  Star,
  Heart,
  Flag,
  Bookmark,
  Tag,
  Tags,
  Grip,
  GripVertical,
  Move,
  Maximize,
  Minimize,
  ZoomIn,
  ZoomOut,
  Crosshair,
  Compass,
  Navigation,
} from "lucide-react";

// =============================================================================
// ICON MAPPING FOR GHG CATEGORIES
// =============================================================================

import type { LucideIcon } from "lucide-react";
import {
  Flame,
  Car,
  Wind,
  Zap,
  Package,
  Droplet,
  Truck,
  Trash2,
  Plane,
  Users,
  Building2,
  Factory,
  Globe,
} from "lucide-react";

/**
 * Maps GHG category codes to their icons
 */
export const categoryIcons: Record<string, LucideIcon> = {
  // Scope 1
  "1.1": Flame, // Stationary Combustion
  "1.2": Car, // Mobile Combustion
  "1.3": Wind, // Fugitive Emissions

  // Scope 2
  "2": Zap, // Purchased Electricity/Energy
  "2.1": Zap, // Electricity
  "2.2": Droplet, // Heat/Steam/Cooling

  // Scope 3
  "3.1": Package, // Purchased Goods & Services
  "3.2": Factory, // Capital Goods
  "3.3": Droplet, // Fuel & Energy Related
  "3.4": Truck, // Upstream Transportation
  "3.5": Trash2, // Waste Generated
  "3.6": Plane, // Business Travel
  "3.7": Users, // Employee Commuting
  "3.8": Building2, // Upstream Leased Assets
  "3.9": Truck, // Downstream Transportation
  "3.10": Package, // Processing of Sold Products
  "3.11": Package, // Use of Sold Products
  "3.12": Trash2, // End-of-life Treatment
  "3.13": Building2, // Downstream Leased Assets
  "3.14": Factory, // Franchises
  "3.15": Globe, // Investments
};

/**
 * Get icon component for a GHG category
 */
export function getCategoryIcon(categoryCode: string): LucideIcon {
  return categoryIcons[categoryCode] || Globe;
}

/**
 * Maps scope numbers to their primary icons
 */
export const scopeIcons: Record<1 | 2 | 3, LucideIcon> = {
  1: Flame,
  2: Zap,
  3: Globe,
};

/**
 * Get icon component for a scope
 */
export function getScopeIcon(scope: 1 | 2 | 3): LucideIcon {
  return scopeIcons[scope];
}

// =============================================================================
// ICON PROPS TYPE
// =============================================================================

export interface IconProps {
  size?: number | string;
  strokeWidth?: number;
  className?: string;
}

export const defaultIconProps: IconProps = {
  size: 20,
  strokeWidth: 2,
};

export const smallIconProps: IconProps = {
  size: 16,
  strokeWidth: 2,
};

export const largeIconProps: IconProps = {
  size: 24,
  strokeWidth: 1.5,
};
