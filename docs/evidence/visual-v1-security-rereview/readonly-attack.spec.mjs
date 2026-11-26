import { expect, test } from "../../../apps/web/node_modules/@playwright/test/index.mjs";

const stored = (page) => page.evaluate(() => sessionStorage.getItem("flip-project"));

test("independent read-only attack: drag, connect, reconnect, delete, clipboard, rapid mode", async ({ page }) => {
	const requests = [];
	const errors = [];
	page.on("request", (r) => requests.push(`${r.method()} ${new URL(r.url()).pathname}`));
	page.on("pageerror", (e) => errors.push(e.message));
	await page.goto("/");
	await page.getByRole("button", { name: /^Open sample/ }).click();
	await page.getByRole("button", { name: "Build netlist", exact: true }).click();
	await expect(page.getByText(/81 bytes · 8 expanded gates/)).toBeVisible();
	await page.getByRole("button", { name: "Visual", exact: true }).click();
	requests.length = 0;

	const before = await stored(page);
	const nodes = page.locator(".react-flow__node");
	const edges = page.locator(".react-flow__edge");
	const nodeCount = await nodes.count();
	const edgeCount = await edges.count();
	expect(nodeCount).toBe(5);
	expect(edgeCount).toBe(8);

	// 1. Drag a node by its body.
	const box = await nodes.first().boundingBox();
	await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
	await page.mouse.down();
	await page.mouse.move(box.x + box.width / 2 + 120, box.y + box.height / 2 + 90, { steps: 8 });
	await page.mouse.up();
	const afterDrag = await nodes.first().boundingBox();
	expect(Math.abs(afterDrag.x - box.x)).toBeLessThan(2);
	expect(Math.abs(afterDrag.y - box.y)).toBeLessThan(2);

	// 2. Attempt to create an edge by dragging a source handle to a target handle.
	const sourceHandle = page.locator('.react-flow__handle[data-handleid^="out:"]').first();
	const targetHandle = page.locator('.react-flow__handle[data-handleid^="in:"]').last();
	const sh = await sourceHandle.boundingBox();
	const th = await targetHandle.boundingBox();
	await page.mouse.move(sh.x + sh.width / 2, sh.y + sh.height / 2);
	await page.mouse.down();
	await page.mouse.move(th.x + th.width / 2, th.y + th.height / 2, { steps: 10 });
	await page.mouse.up();
	await expect(nodes).toHaveCount(nodeCount);
	await expect(edges).toHaveCount(edgeCount);

	// 3. Attempt edge reconnect by dragging its endpoint.
	const edgePath = page.locator(".react-flow__edge-path").first();
	const eb = await edgePath.boundingBox();
	await page.mouse.move(eb.x + 2, eb.y + 2);
	await page.mouse.down();
	await page.mouse.move(eb.x + 120, eb.y + 80, { steps: 8 });
	await page.mouse.up();
	await expect(edges).toHaveCount(edgeCount);

	// 4. Select a node and attempt Delete, Backspace and clipboard shortcuts.
	await nodes.nth(1).click();
	for (const key of ["Delete", "Backspace", "Control+x", "Control+c", "Control+v", "Control+z"])
		await page.keyboard.press(key);
	await expect(nodes).toHaveCount(nodeCount);
	await expect(edges).toHaveCount(edgeCount);

	// 5. Inspector interactions must only change selection, never the request.
	await page.getByLabel("Inspect component", { exact: true }).selectOption({ index: 3 });
	await page.getByLabel("Inspect pin", { exact: true }).selectOption({ index: 1 });
	await expect(page.locator(".visual-inspector [role='status']")).toBeVisible();

	// 6. Rapid mode switching and repeated StrictMode remounts.
	for (let i = 0; i < 12; i++) {
		await page.getByRole("button", { name: "Advanced", exact: true }).click();
		await page.getByRole("button", { name: "Visual", exact: true }).click();
	}
	await expect(nodes).toHaveCount(nodeCount);
	await expect(edges).toHaveCount(edgeCount);

	// 7. Unsupported event combinations: pan while modifier keys held, wheel zoom.
	await page.keyboard.down("Shift");
	await page.mouse.move(600, 600);
	await page.mouse.wheel(0, -200);
	await page.keyboard.up("Shift");

	expect(await stored(page)).toBe(before);
	expect(requests).toEqual([]);
	expect(errors).toEqual([]);
});
