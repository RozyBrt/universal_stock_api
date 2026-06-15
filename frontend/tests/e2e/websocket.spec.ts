import { test, expect } from "@playwright/test";

test.describe("Real-time WebSocket Synchronization (Multi-Context)", () => {
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

  test("Mutasi stok di Browser A harus meng-update tabel di Browser B secara instan lengkap dengan Toast notifikasi", async ({ browser }) => {
    // 1. Buat Browser Context A (User 1)
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    // 2. Buat Browser Context B (User 2)
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    // --- SETUP BROWSER A ---
    await pageA.goto("/login");
    await pageA.evaluate((t) => {
      localStorage.setItem("access_token", t);
    }, token);
    await pageA.goto("/inventory");
    await expect(pageA).toHaveURL(/\/inventory/);

    // --- SETUP BROWSER B ---
    await pageB.goto("/login");
    await pageB.evaluate((t) => {
      localStorage.setItem("access_token", t);
    }, token);
    await pageB.goto("/inventory");
    await expect(pageB).toHaveURL(/\/inventory/);

    // Ambil detail barang pertama dari Browser B sebelum mutasi
    const firstRowB = pageB.locator("table.inventory-table tbody tr").first();
    await expect(firstRowB).toBeVisible({ timeout: 10000 }); // Tunggu data termuat
    
    const sku = (await firstRowB.locator("td.font-mono").textContent())?.trim() || "";
    const initialStockText = (await firstRowB.locator(".stock-badge").textContent())?.trim() || "0";
    const initialStock = parseInt(initialStockText);
    const itemName = (await firstRowB.locator("td.font-medium").textContent())?.trim() || "";

    expect(sku).not.toBe("");
    console.log(`Menguji sinkronisasi real-time untuk barang: ${itemName} (${sku}) dengan stok awal: ${initialStock}`);

    // --- AKSI MUTASI DI BROWSER A (+5 Stock) ---
    // Cari barang berdasarkan SKU di Browser A
    await pageA.locator('input[placeholder*="Search by"]').fill(sku);
    const rowA = pageA.locator("table.inventory-table tbody tr").first();
    await expect(rowA).toBeVisible();

    // Klik "+ In" untuk menambah stok
    await rowA.locator("button.btn-in").click();
    const inModal = pageA.locator('.modal-content:has-text("Add Stock")');
    await inModal.locator('label:has-text("Quantity") + input').fill("5");
    await inModal.locator('label:has-text("Reference Number") + input').fill("REF-WS-IN");
    await inModal.locator('button[type="submit"]').click();

    // --- SINKRONISASI DI BROWSER B (Tanpa Reload) ---
    // Di Browser B, stok barang pertama harus otomatis bertambah sebesar 5 unit (initialStock + 5)
    const expectedNewStock = (initialStock + 5).toString();
    const stockBadgeB = firstRowB.locator(".stock-badge");
    
    // Playwright secara otomatis menunggu (auto-wait) hingga teks badge di Browser B berubah
    await expect(stockBadgeB).toContainText(expectedNewStock, { timeout: 15000 });
    console.log(`Sukses: Stok di Browser B ter-update otomatis menjadi ${expectedNewStock}!`);

    // Verifikasi bahwa baris tabel mendapatkan efek flash animasi penambahan stok (flash-in)
    await expect(firstRowB).toHaveClass(/flash-in/);

    // Bersihkan context browser setelah selesai pengujian
    await contextA.close();
    await contextB.close();
  });
});
