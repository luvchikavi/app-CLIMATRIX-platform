import { redirect } from 'next/navigation';

/**
 * The GHG Inventory module was retired as a separate surface — it duplicated
 * Reports. The route stays alive so old links keep working.
 */
export default function GHGModulePage() {
  redirect('/reports');
}
