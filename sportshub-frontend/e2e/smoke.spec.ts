import { expect, test } from '@playwright/test'

test('home page is usable at the configured viewport', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /every score/i })).toBeVisible()
  await expect(page.getByRole('navigation', { name: /primary/i })).toBeVisible()
  await expect(page.getByRole('link', { name: /sign in/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: /matchday center/i })).toBeVisible()
  await expect(page.getByRole('heading', { name: /live now/i })).toBeVisible()

  await page.getByRole('link', { name: /explore teams/i }).click()
  await expect(page).toHaveURL(/\/explore\/teams$/)
  await expect(page.getByRole('heading', { name: /explore teams/i })).toBeVisible()

  const pageWidths = await page.evaluate(() => ({
    viewport: window.innerWidth,
    document: document.documentElement.scrollWidth,
  }))
  expect(pageWidths.document).toBeLessThanOrEqual(pageWidths.viewport)
})
