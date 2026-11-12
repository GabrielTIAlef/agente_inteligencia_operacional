import assert from 'node:assert/strict'
import { mkdir, readFile } from 'node:fs/promises'
import { test } from 'node:test'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core')
const site = process.env.DEMO_URL || 'http://127.0.0.1:5173'
const evidence = process.env.DEMO_SCREENSHOTS

test('filtros automáticos, exportação aprovada, monitor e chat com API real', async () => {
  const browser = await chromium.launch({ channel: 'msedge' })
  try {
    if (evidence) await mkdir(evidence, { recursive: true })
    for (const width of [1440, 768, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 940 } })
      await page.goto(site)
      await page.getByRole('heading', { name: 'Ranking por região' }).waitFor()
      await page.getByRole('heading', { name: 'Relatório operacional' }).waitFor()
      assert.equal(await page.locator('.dashboard-results > .metrics dd').count(), 5)
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
      if (evidence) await page.screenshot({ path: evidence + '/painel-' + width + '.png', fullPage: true })
      const region = page.getByRole('combobox', { name: 'Região', exact: true })
      const option = await region.locator('option').nth(1).textContent()
      const response = page.waitForResponse(r => r.url().includes('/operations/dashboard?') && new URL(r.url()).searchParams.get('region') === option)
      await region.selectOption({ label: option })
      assert.equal((await response).status(), 200)
      const delivered = page.getByRole('button', { name: /^Entregues/ })
      const statusResponse = page.waitForResponse(r => r.url().includes('/operations/dashboard?') && new URL(r.url()).searchParams.get('status') === 'entregue')
      await delivered.click()
      assert.equal((await statusResponse).status(), 200)
      await page.locator('.content-card .export-scope').filter({ hasText: 'Entregues' }).waitFor()
      await page.getByRole('button', { name: 'Atualizar prévia', exact: true }).waitFor({ state: 'visible' })
      const approval = page.getByRole('checkbox', { name: /Aprovo/ })
      const download = page.getByRole('button', { name: 'Baixar relatório JSON', exact: true })
      assert.ok(await download.isDisabled())
      await approval.check()
      const [file] = await Promise.all([page.waitForEvent('download'), download.click()])
      const report = JSON.parse(await readFile(await file.path(), 'utf8'))
      assert.equal(report.source, 'postgresql')
      assert.equal(report.scope.region, option)
      assert.equal(report.scope.status, 'entregue')
      assert.equal(report.summary.total_pedidos, Number((await page.locator('.dashboard-results > .metrics dd').first().textContent()).replaceAll('.', '')))
      assert.ok(await download.isDisabled())
      await page.getByRole('button', { name: 'Monitoramento', exact: true }).click()
      await page.getByRole('heading', { name: 'Histórico de execuções' }).waitFor()
      if (evidence && width === 1440) await page.screenshot({ path: evidence + '/monitoramento.png', fullPage: true })
      await page.getByRole('button', { name: '✦ Conversar com IA', exact: true }).click()
      await page.getByRole('textbox', { name: 'Sua pergunta', exact: true }).waitFor()
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
      if (evidence && width === 1440) await page.screenshot({ path: evidence + '/chat.png', fullPage: true })
      await page.getByRole('textbox', { name: 'Sua pergunta', exact: true }).press('Escape')
      assert.ok(await page.getByRole('button', { name: '✦ Conversar com IA', exact: true }).isVisible())
      await page.close()
    }
  } finally {
    await browser.close()
  }
})
