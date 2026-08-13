import { expect, test } from '@playwright/test'

test('home page is usable at the configured viewport', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /every score/i })).toBeVisible()
  await expect(page.getByRole('navigation', { name: /primary/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: /matchday center/i })).toBeVisible()
  await expect(page.getByText(/api allowance|cache hit|daily api requests/i)).toHaveCount(0)
  await expect(page.getByRole('tablist', { name: /fixture status/i })).toBeVisible()
  await expect(page.getByLabel(/choose match date/i)).toBeVisible()
  await expect(page.getByLabel(/fixture pagination/i)).toBeVisible()

  const firstFixture = page.getByRole('link', { name: /view .* fixture details/i }).first()
  if (await firstFixture.count()) {
    await firstFixture.click()
    await expect(page).toHaveURL(/\/fixtures\/\d+\?date=/)
    await expect(page.getByRole('tablist', { name: /fixture details/i })).toBeVisible()
    await page.getByRole('tab', { name: /statistics/i }).click()
    await expect(page.getByRole('heading', { name: /match statistics/i })).toBeVisible()
    await page.getByRole('tab', { name: /lineups/i }).click()
    await expect(page.getByRole('heading', { name: /lineups/i })).toBeVisible()
    await page.getByRole('tab', { name: /timeline/i }).click()
    await expect(page.getByRole('heading', { name: /match timeline/i })).toBeVisible()
    await page.getByRole('tab', { name: /chat/i }).click()
    await expect(page.getByRole('heading', { name: /match chat is coming soon/i })).toBeVisible()
    await expect(page.getByText(/api allowance|cache hit|daily api requests/i)).toHaveCount(0)
    await page.goBack()
    await expect(page.getByRole('heading', { name: /matchday center/i })).toBeVisible()
  }

  await page.getByRole('link', { name: /explore teams/i }).click()
  await expect(page).toHaveURL(/\/explore\/teams$/)
  await expect(page.getByRole('heading', { name: /explore teams/i })).toBeVisible()

  const pageWidths = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
  }))
  expect(pageWidths.document).toBeLessThanOrEqual(pageWidths.viewport)
})
