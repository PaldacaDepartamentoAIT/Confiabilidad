import {
  Bell,
  Building2,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsUpDown,
  CircleAlert,
  Eye,
  EyeOff,
  Factory,
  FileText,
  Globe,
  House,
  Info,
  Menu,
  Moon,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  Sun,
  Wrench,
  type LucideIcon,
  type LucideProps,
} from "lucide-react";
import { createElement } from "react";

// Iconos de la guía: 16 px y trazo 2 por defecto; el tamaño se puede cambiar (el botón del menú usa 22 px).
function sized(icon: LucideIcon, displayName: string) {
  const Sized = (props: LucideProps) =>
    createElement(icon, { size: 16, strokeWidth: 2, "aria-hidden": true, ...props });
  Sized.displayName = displayName;
  return Sized;
}

export const IconAlert = sized(CircleAlert, "IconAlert");
export const IconBell = sized(Bell, "IconBell");
export const IconBuilding = sized(Building2, "IconBuilding");
export const IconCheck = sized(Check, "IconCheck");
export const IconChevronDown = sized(ChevronDown, "IconChevronDown");
export const IconChevronLeft = sized(ChevronLeft, "IconChevronLeft");
export const IconChevronRight = sized(ChevronRight, "IconChevronRight");
export const IconChevronsUpDown = sized(ChevronsUpDown, "IconChevronsUpDown");
export const IconEye = sized(Eye, "IconEye");
export const IconEyeOff = sized(EyeOff, "IconEyeOff");
export const IconFactory = sized(Factory, "IconFactory");
export const IconFile = sized(FileText, "IconFile");
export const IconGlobe = sized(Globe, "IconGlobe");
export const IconHouse = sized(House, "IconHouse");
export const IconInfo = sized(Info, "IconInfo");
export const IconMenu = sized(Menu, "IconMenu");
export const IconMoon = sized(Moon, "IconMoon");
export const IconPackage = sized(Package, "IconPackage");
export const IconPanelClose = sized(PanelLeftClose, "IconPanelClose");
export const IconPanelOpen = sized(PanelLeftOpen, "IconPanelOpen");
export const IconSearch = sized(Search, "IconSearch");
export const IconSettings = sized(Settings, "IconSettings");
export const IconSun = sized(Sun, "IconSun");
export const IconWrench = sized(Wrench, "IconWrench");
