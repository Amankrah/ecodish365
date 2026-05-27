import { redirect } from 'next/navigation';

/** Retired — population HENI dashboard removed; scorecard covers multi-metric policy view. */
export default function HENIPolicyDashboardRedirect() {
  redirect('/scorecard');
}
