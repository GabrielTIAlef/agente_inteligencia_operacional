import assert from 'node:assert/strict'
import { mkdir, readFile } from 'node:fs/promises'
import { test } from 'node:test'

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright-core')
const site = process.env.DEMO_URL || 'http://127.0.0.1:5173'
const evidence = process.env.DEMO_SCREENSHOTS

test('boletim, filtros e monitor com API real em três larguras', async () => {
  const browser = await chromium.launch({ channel: 'msedge' })
  try {
    if (evidence) await mkdir(evidence, { recursive: true })
    for (const width of [1440, 768, 390]) {
      const page = await browser.newPage({ viewport: { width, height: 940 } })
      await page.goto(site)
      await page.getByRole('heading', { name: 'Volume por região' }).waitFor()
      await page.getByRole('heading', { name: 'Volume por categoria' }).waitFor()
      assert.equal(await page.locator('.metrics dd').count(), 5)
      await page.getByRole('heading', { name: 'Comparação com a janela anterior' }).waitFor()
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
      if (evidence) await page.screenshot({ path: evidence + '/boletim-' + width + '.png', fullPage: true })
      const region = page.getByLabel('Região')
      const options = await region.locator('option').allTextContents()
      assert.ok(options.length > 1)
      await region.selectOption({ label: options[1] })
      const response = page.waitForResponse((result) => result.url().includes('/operations/dashboard?'))
      await page.getByRole('button', { name: 'Aplicar' }).click()
      assert.equal((await response).status(), 200)
      await page.getByRole('heading', { name: 'Volume por região' }).waitFor()
      await page.getByRole('button', { name: 'Monitoramento' }).click()
      await page.getByRole('heading', { name: 'Registro de execuções' }).waitFor()
      if (evidence && width === 1440) await page.screenshot({ path: evidence + '/monitoramento.png', fullPage: true })
      if (width === 390) {
        await page.getByText('Exportar prévia operacional').click()
        const download = page.getByRole('button', { name: 'Baixar relatório JSON' })
        await download.waitFor()
        assert.ok(await download.isDisabled())
        await page.getByRole('checkbox', { name: /Aprovo/ }).check()
        const [file] = await Promise.all([page.waitForEvent('download'), download.click()])
        assert.equal(JSON.parse(await readFile(await file.path(), 'utf8')).source, 'postgresql')
        assert.ok(await download.isDisabled())
        await page.getByRole('button', { name: 'Assistente de dados' }).click()
        await page.getByRole('textbox', { name: 'Sua pergunta' }).waitFor()
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true)
      }
      if (width === 1440 && evidence) {
        await page.getByRole('button', { name: 'Assistente de dados' }).click()
        await page.getByRole('textbox', { name: 'Sua pergunta' }).waitFor()
        await page.screenshot({ path: evidence + '/assistente.png', fullPage: true })
      }
      await page.close()
    }
  } finally {
    await browser.close()
  }
})
