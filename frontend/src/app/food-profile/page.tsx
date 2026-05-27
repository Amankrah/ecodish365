/**
 * /food-profile → /scorecard
 *
 * SCORECARD-1 (2026-05-26): the multi-metric food-profile view was renamed
 * `/scorecard` at ship time, but the nav had been advertising `/food-profile`
 * during development. This route is kept as a permanent redirect so any
 * bookmarks, prior chat / docs links, or in-progress UI references keep working.
 *
 * Note: the per-scorer drill-downs `/hsr/food-profile`, `/hefi/food-profile`,
 * `/fcs/food-profile` are unrelated single-food pages and stay where they are.
 */
import { redirect } from 'next/navigation';

export default function FoodProfileRedirect(): never {
  redirect('/scorecard');
}
