import { test, expect } from "@playwright/test";

test.describe("Autentikasi (Authentication Flow)", () => {
  test.beforeEach(async ({ page }) => {
    // Navigasi ke halaman login sebelum setiap tes
    await page.goto("/login");
  });

  test("Gagal login dengan kredensial yang salah", async ({ page }) => {
    // Isi form dengan data salah
    await page.locator('input[type="email"]').fill("wronguser@example.com");
    await page.locator('input[type="password"]').fill("WrongPassword123");
    
    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verifikasi pesan error muncul di UI
    const errorAlert = page.locator(".alert-error");
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText(/salah|failed|incorrect/i);
  });

  test("Berhasil login dengan akun demo admin", async ({ page }) => {
    // Isi form dengan kredensial demo admin yang valid
    await page.locator('input[type="email"]').fill("demo@example.com");
    await page.locator('input[type="password"]').fill("Password1");

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verifikasi diarahkan ke dashboard
    await expect(page).toHaveURL(/\/dashboard/);
    
    // Verifikasi token tersimpan di localStorage
    const token = await page.evaluate(() => localStorage.getItem("access_token"));
    expect(token).not.toBeNull();
    expect(token?.length).toBeGreaterThan(10);
  });

  test("Berhasil melakukan logout", async ({ page }) => {
    // Login terlebih dahulu
    await page.locator('input[type="email"]').fill("demo@example.com");
    await page.locator('input[type="password"]').fill("Password1");
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Temukan tombol Logout di sidebar dan klik
    await page.locator("button:has-text('Logout')").click();

    // Verifikasi diarahkan kembali ke halaman login
    await expect(page).toHaveURL(/\/login/);

    // Verifikasi token access_token di localStorage telah dihapus
    const token = await page.evaluate(() => localStorage.getItem("access_token"));
    expect(token).toBeNull();
  });
});
