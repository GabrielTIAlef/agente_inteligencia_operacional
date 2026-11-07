import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core')
const site = process.env.DEMO_URL || 'http://127.0.0.1:5173'

test('dashboard real, navegação móvel e aprovação de exportação', async () => {
  const browser = await chromium.launch({ channel: 'msedge' })
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
    await page.goto(site)
    await page.getByRole('heading', { name: 'Pedidos por região' }).waitFor()
    await page.getByRole('heading', { name: 'Pedidos por categoria' }).waitFor()
    assert.equal(await page.locator('.metric-card').count(), 4)
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)

    await page.getByRole('button', { name: 'Automações' }).click()
    const download = page.getByRole('button', { name: 'Baixar relatório JSON' })
    assert.equal(await download.isDisabled(), true)
    const approval = page.getByRole('checkbox', { name: 'Aprovo a exportação local desta prévia' })
    await approval.check()
    assert.equal(await download.isEnabled(), true)
    await page.getByRole('button', { name: 'Atualizar prévia' }).click()
    await download.waitFor()
    assert.equal(await download.isDisabled(), true)

    await approval.check()
    const [file] = await Promise.all([page.waitForEvent('download'), download.click()])
    const report = JSON.parse(await readFile(await file.path(), 'utf8'))
    assert.equal(report.source, 'postgresql')
    assert.equal(file.suggestedFilename(), `relatorio-operacional-${report.request_id}.json`)
    assert.equal(await download.isDisabled(), true)

    await page.getByRole('button', { name: 'Chat com IA' }).click()
    await page.route('**/agent/chat', async (route) => {
      if (route.request().method() !== 'POST') return route.continue()
      assert.equal(route.request().postDataJSON().message, 'Quantos pedidos existem?')
      await route.fulfill({
        status: 503,
        headers: { 'Access-Control-Expose-Headers': 'X-Request-ID', 'X-Request-ID': 'teste-navegador' },
        json: { detail: 'Agente indisponível na simulação.' },
      })
    })
    await page.getByRole('textbox', { name: 'Sua pergunta' }).fill('Quantos pedidos existem?')
    await page.getByRole('button', { name: 'Enviar' }).click()
    await page.getByText('Agente indisponível na simulação. Referência: teste-navegador.').waitFor()
  } finally {
    await browser.close()
  }
})
