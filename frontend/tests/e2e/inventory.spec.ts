import { test, expect } from "@playwright/test";

test.describe("Manajemen Inventaris (Inventory Management Flow)", () => {
  const testSKU = `PW-SKU-${Math.floor(Math.random() * 9000) + 1000}`;
  const testItemName = "Playwright Test Item";
  let token: string;

  test.beforeAll(async () => {
    // Ambil token JWT langsung via API untuk mempercepat tes dan menghindari pembatasan rate limit login
    const response = await fetch("http://localhost:8000/api/v1/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: "username=demo%40example.com&password=Password1",
    });
    if (!response.ok) {
      throw new Error(`Failed to pre-fetch auth token: ${response.statusText}`);
    }
    const data = (await response.json()) as any;
    token = data.access_token;
  });

  test.beforeEach(async ({ page }) => {
    // Inject token langsung ke localStorage dan arahkan ke halaman inventaris
    await page.goto("/login");
    await page.evaluate((t) => {
      localStorage.setItem("access_token", t);
    }, token);
    await page.goto("/inventory");
    await expect(page).toHaveURL(/\/inventory/);
    // Tunggu hingga skeleton loading selesai
    await expect(page.locator("table.inventory-table tbody .skeleton").first()).not.toBeVisible({ timeout: 15000 });
  });


  test("Berhasil membuat barang baru", async ({ page }) => {
    // Buka modal item baru
    await page.locator('button:has-text("New Item")').click();

    // Isi formulir barang baru
    await page.locator('label:has-text("Name") + input').fill(testItemName);
    await page.locator('label:has-text("SKU") + input').fill(testSKU);
    await page.locator('label:has-text("Unit Price") + input').fill("12500");
    await page.locator('label:has-text("Initial Stock") + input').fill("25");
    await page.locator('label:has-text("Reorder Level") + input').fill("10");
    await page.locator('label:has-text("Description") + textarea').fill("Item deskripsi pengujian Playwright");

    // Submit
    await page.locator('.modal-content button:has-text("Create Item")').click();

    // Cari barang yang baru dibuat di tabel untuk memverifikasi kesuksesan
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    const row = page.locator("table.inventory-table tbody tr").first();
    await expect(row.locator("td.font-medium")).toContainText(testItemName);
    await expect(row.locator(".stock-badge")).toContainText("25");
  });

  test("Berhasil melakukan mutasi stok IN & OUT", async ({ page }) => {
    // Cari barang pengujian
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    const row = page.locator("table.inventory-table tbody tr").first();
    await expect(row).toBeVisible();

    // ---- MUTASI IN (+15) ----
    await row.locator("button.btn-in").click();
    
    // Isi jumlah penambahan
    const inModal = page.locator('.modal-content:has-text("Add Stock")');
    await inModal.locator('label:has-text("Quantity") + input').fill("15");
    await inModal.locator('label:has-text("Reference Number") + input').fill("REF-IN-PW");
    await inModal.locator('button[type="submit"]').click();

    // Verifikasi stok bertambah dari 25 menjadi 40
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    await expect(row.locator(".stock-badge")).toContainText("40");

    // ---- MUTASI OUT (-12) ----
    await row.locator("button.btn-out").click();
    
    // Isi jumlah pengurangan
    const outModal = page.locator('.modal-content:has-text("Remove Stock")');
    await outModal.locator('label:has-text("Quantity") + input').fill("12");
    await outModal.locator('label:has-text("Reference Number") + input').fill("REF-OUT-PW");
    await outModal.locator('button[type="submit"]').click();

    // Verifikasi stok berkurang menjadi 28 (40 - 12)
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    await expect(row.locator(".stock-badge")).toContainText("28");
  });

  test("Berhasil mengedit informasi barang", async ({ page }) => {
    // Cari barang pengujian
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    const row = page.locator("table.inventory-table tbody tr").first();
    
    // Buka modal edit
    await row.locator('button[title="Edit Item"]').click();

    // Ubah nama dan batas minimum order
    const editModal = page.locator('.modal-content:has-text("Edit Item")');
    await editModal.locator('label:has-text("Name") + input').fill(testItemName + " (Updated)");
    await editModal.locator('label:has-text("Reorder Level") + input').fill("15");
    await editModal.locator('button[type="submit"]').click();

    // Verifikasi perubahan tersimpan
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    await expect(row.locator("td.font-medium")).toContainText(testItemName + " (Updated)");
  });

  test("Berhasil menghapus (soft delete) barang", async ({ page }) => {
    // Cari barang pengujian
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    const row = page.locator("table.inventory-table tbody tr").first();

    // Klik hapus
    await row.locator('button[title="Delete Item"]').click();
    
    // Konfirmasi di modal hapus
    await page.locator(".modal-content button:has-text('Ya, Hapus')").click();

    // Verifikasi barang tidak lagi muncul di tabel inventaris
    await page.locator('input[placeholder*="Search by"]').fill(testSKU);
    await expect(page.locator("table.inventory-table tbody td.empty-state")).toBeVisible();
  });
});
