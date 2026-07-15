/**
 * Canopy — the Console × Guide component kit (DESIGN-REVISION-PLAN.md §2.3).
 * Coexists with components/ui/ until batch 2.7; page batches switch imports.
 */
export { Surface, PanelLabel, type SurfaceProps } from './Surface';
export { CanopyButton, type CanopyButtonProps } from './Button';
export {
  Rail,
  Logo,
  type RailProps,
  type RailJourneyStep,
  type RailNavItem,
  type RailNavGroup,
  type JourneyStepState,
} from './Rail';
export { Shell, PageHead, type ShellProps } from './Shell';
export { FocusCard, type FocusCardProps } from './FocusCard';
export { StatCells, type StatCell } from './StatCells';
export { BarList, type BarListItem } from './BarList';
export { TaskList, type TaskItem } from './TaskList';
export {
  StepRow,
  StepDoneText,
  StepLockedText,
  StepValue,
  type StepRowProps,
} from './StepRow';
export { PillTabs, type PillTab } from './PillTabs';
export { Chip, ChipGroup, type ChipProps } from './Chip';
export { FinishBar, type FinishBarProps } from './FinishBar';
export { DataTable, CellValue, ShareBar, type CanopyColumn } from './DataTable';
export { canopyChart } from './chartTheme';
export { canopyFont } from './font';
