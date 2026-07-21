import { redirect } from 'next/navigation';

/** EPD graduated from the coming-soon catalog to a real tool at /epd. */
export default function EPDModulePage() {
  redirect('/epd');
}
