import { redirect } from 'next/navigation';

/** PCF went live as the /products module — keep old links working. */
export default function PCFModulePage() {
  redirect('/products');
}
