import { redirect } from 'next/navigation';

/** LCA-lite went live inside the PCF product pages — keep old links working. */
export default function LCAModulePage() {
  redirect('/products');
}
