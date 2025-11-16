// frontend/game.js
(function () {
  // -----------------------------
  // Session / backend integration
  // -----------------------------
  const sessionId = localStorage.getItem("session_id");
  if (!sessionId) {
    // If there is no session, send them back to notes page
    window.location.href = "page2.html";
    return;
  }
  console.log("Using session:", sessionId);

  const API_BASE = "http://127.0.0.1:5000"; // adjust if your Flask host/port differ

  // Selected character from person.html
  const selectedGhostImagePath = localStorage.getItem("selectedGhostImage") || null;
  let selectedGhostImage = null;
  if (selectedGhostImagePath) {
    selectedGhostImage = new Image();
    selectedGhostImage.src = selectedGhostImagePath;
  }

  // -----------------------------
  // Canvas setup
  // -----------------------------
  const canvas = document.getElementById("game-canvas");
  const ctx = canvas.getContext("2d");

  const TILE = 32;
  const COLS = Math.floor(canvas.width / TILE);
  const ROWS = Math.floor(canvas.height / TILE);

  // -----------------------------
  // Map layout
  // W = wall, . = pumpkin, P = player, E = enemy, F = family, C = checkpoint
  // -----------------------------
  const RAW_MAP = [
    "WWWWWWWWWWWWWWWWWWWWWWWWW",
    "W....C........W....C....W",
    "W.WWW.WWWWWWW.W.WWWWW.W.W",
    "W.P..W.......W.W.....W.WW",
    "W.WWW.WWWWW.WW.W.WWW.W..W",
    "W.....W...W....W.W...W..W",
    "WWWWW.W.W.WWWWWW.W.W.W..W",
    "W.....W.W....E.....W....W",
    "W.WWWWW.WWWWWWWWWWWW.WWWW",
    "W.W.....W...........W..FW",
    "W.W.WWWWW.WWWWWWWWW.W.W.W",
    "W...W.....W.......W...W.W",
    "WWW.W.WWWWW.WWWWW.WWW.W.W",
    "W...W.W.....W.....W...W.W",
    "W.WWW.W.WWW.W.WWW.W.WWW.W",
    "W.W...W.W...W.W...W.W...W",
    "W.W.WWW.WWWWW.WWWWW.W.W.W",
    "W.W.W....C..........W.W.W",
    "W.W.WWWWWWWWWWWWWWWWW.W.W",
    "W.W...................W.W",
    "W.WWWWWWWWWWWWWWWWWWWWW.W",
    "W.F.................F..FW",
    "WWWWWWWWWWWWWWWWWWWWWWWWW"
  ];

  const MAP = [];
  for (let r = 0; r < ROWS; r++) {
    const line = RAW_MAP[r] || "";
    const padded = line.padEnd(COLS, "W");
    MAP.push(padded.slice(0, COLS));
  }

  // -----------------------------
  // Game state
  // -----------------------------
  const game = {
    player: null,
    enemy: null,
    walls: [],
    pumpkins: [],
    family: [],
    checkpoints: [],
    points: 0,
    running: true,
    ended: false
  };

  // -----------------------------
  // DOM references for overlay
  // -----------------------------
  const checkpointOverlay = document.getElementById("checkpoint-overlay");
  const checkpointTitle = document.getElementById("checkpoint-title");
  const checkpointCards = document.getElementById("checkpoint-cards");
  const checkpointClose = document.getElementById("checkpoint-close");

  checkpointClose.addEventListener("click", () => {
    checkpointOverlay.classList.add("hidden");
    game.running = true;
  });

  // -----------------------------
  // Base entity
  // -----------------------------
  class RectEntity {
    constructor(x, y, w, h) {
      this.x = x;
      this.y = y;
      this.w = w;
      this.h = h;
    }
    get cx() {
      return this.x + this.w / 2;
    }
    get cy() {
      return this.y + this.h / 2;
    }
    intersects(other) {
      return !(
        this.x + this.w <= other.x ||
        this.x >= other.x + other.w ||
        this.y + this.h <= other.y ||
        this.y >= other.y + other.h
      );
    }
  }

  // -----------------------------
  // Player
  // -----------------------------
  class Player extends RectEntity {
    constructor(x, y) {
      super(x, y, TILE * 0.8, TILE * 0.8);
      this.speed = 5;
      this.color = "#7fffff";
    }

    handleInput(keys) {
      if (!game.running) return;
      let dx = 0, dy = 0;
      if (keys["ArrowLeft"]) dx -= this.speed;
      if (keys["ArrowRight"]) dx += this.speed;
      if (keys["ArrowUp"]) dy -= this.speed;
      if (keys["ArrowDown"]) dy += this.speed;
      this.move(dx, dy);
    }

    move(dx, dy) {
      // X movement
      this.x += dx;
      if (collidesWithWalls(this)) this.x -= dx;

      // Y movement
      this.y += dy;
      if (collidesWithWalls(this)) this.y -= dy;
    }

    draw(ctx) {
      if (selectedGhostImage && selectedGhostImage.complete) {
        ctx.drawImage(selectedGhostImage, this.x, this.y, this.w, this.h);
      } else {
        // fallback: simple ghost shape
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.cx, this.cy, this.w / 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillRect(this.x, this.y + this.h * 0.3, this.w, this.h * 0.7);
      }
    }
  }

  // -----------------------------
  // Enemy ghost
  // -----------------------------
  class Enemy extends RectEntity {
    constructor(x, y) {
      super(x, y, TILE * 0.8, TILE * 0.8);
      this.speed = 1.5;
      this.color = "#ff4081";
    }

    update() {
      if (!game.running || !game.player) return;

      const target = game.player;
      let dx = 0, dy = 0;

      if (Math.abs(target.cx - this.cx) > 1) {
        dx = target.cx > this.cx ? this.speed : -this.speed;
      }
      if (Math.abs(target.cy - this.cy) > 1) {
        dy = target.cy > this.cy ? this.speed : -this.speed;
      }

      this.x += dx;
      if (collidesWithWalls(this)) this.x -= dx;

      this.y += dy;
      if (collidesWithWalls(this)) this.y -= dy;

      if (this.intersects(target)) {
        endGame("caught");
      }
    }

    draw(ctx) {
      ctx.fillStyle = this.color;
      ctx.beginPath();
      ctx.arc(this.cx, this.cy, this.w / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillRect(this.x, this.y + this.h * 0.3, this.w, this.h * 0.7);
    }
  }

  // -----------------------------
  // Walls
  // -----------------------------
  class Wall extends RectEntity {
    draw(ctx) {
      ctx.fillStyle = "#222244";
      ctx.fillRect(this.x, this.y, this.w, this.h);
    }
  }

  // -----------------------------
  // Pumpkins (points)
  // -----------------------------
  class Pumpkin extends RectEntity {
    constructor(x, y) {
      super(x + TILE * 0.25, y + TILE * 0.25, TILE * 0.5, TILE * 0.5);
      this.points = 5;
    }
    draw(ctx) {
      ctx.fillStyle = "#ffa500";
      ctx.beginPath();
      ctx.arc(this.cx, this.cy, this.w / 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // -----------------------------
  // Family members
  // -----------------------------
  class FamilyMember extends RectEntity {
    constructor(x, y) {
      super(x + TILE * 0.1, y + TILE * 0.1, TILE * 0.8, TILE * 0.8);
      this.collected = false;
      this.icon_x = 490;
      this.icon_y = 740;
      this.icon_spacing = 40;
      this.color = "#a6ffcb";
    }

    draw(ctx) {
      if (this.collected) return;
      ctx.fillStyle = this.color;
      ctx.fillRect(this.x, this.y, this.w, this.h);
      ctx.fillStyle = "#000000";
      ctx.font = "10px 'Press Start 2P', monospace";
      ctx.fillText("F", this.x + 4, this.y + 14);
    }

    drawCollectedIcon(ctx, offsetIndex) {
      const x = this.icon_x + (offsetIndex * this.icon_spacing);
      const y = this.icon_y;
      ctx.fillStyle = this.color;
      ctx.fillRect(x, y, TILE * 0.8, TILE * 0.8);
      ctx.fillStyle = "#000000";
      ctx.font = "10px 'Press Start 2P', monospace";
      ctx.fillText("F", x + 4, y + 14);
    }
  }

  // -----------------------------
  // Checkpoints (flashcards)
  // -----------------------------
  class Checkpoint extends RectEntity {
    constructor(x, y, lesson, checkpointIndex) {
      super(x + TILE * 0.25, y + TILE * 0.25, TILE * 0.5, TILE * 0.5);
      this.lesson = lesson;
      this.checkpointIndex = checkpointIndex;
      this.triggered = false;
    }

    draw(ctx) {
      if (this.triggered) return;
      ctx.fillStyle = "#3ef0ff";
      ctx.beginPath();
      ctx.arc(this.cx, this.cy, this.w / 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // -----------------------------
  // Helpers
  // -----------------------------
  function collidesWithWalls(ent) {
    return game.walls.some(w => ent.intersects(w));
  }

  function endGame(reason) {
    if (game.ended) return;
    game.ended = true;
    game.running = false;

    const collected = game.family.filter(f => f.collected).length;
    const total = game.family.length;

    localStorage.setItem("finalScore", String(game.points));
    localStorage.setItem("collectedFamilyCount", String(collected));
    localStorage.setItem("totalFamilyCount", String(total));
    localStorage.setItem("endReason", reason);

    window.location.href = "gameover.html";
  }

  async function showCheckpoint(cp) {
    if (cp.triggered) return;
    cp.triggered = true;
    game.running = false;

    checkpointTitle.textContent = `Lesson ${cp.lesson} – Checkpoint ${cp.checkpointIndex + 1}`;
    checkpointCards.innerHTML = "Loading flashcards...";

    try {
      const url =
        `${API_BASE}/checkpoint?` +
        `session_id=${encodeURIComponent(sessionId)}` +
        `&lesson=${cp.lesson}` +
        `&checkpoint=${cp.checkpointIndex}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const cards = data.flashcards || [];
      if (!cards.length) {
        checkpointCards.innerHTML = "<p>No flashcards returned yet.</p>";
      } else {
        checkpointCards.innerHTML = "";
        for (const fc of cards) {
          const div = document.createElement("div");
          div.className = "checkpoint-card";
          div.innerHTML = `
            <h3>${fc.front}</h3>
            <p>${fc.back}</p>
          `;
          checkpointCards.appendChild(div);
        }
      }
    } catch (err) {
      console.error(err);
      checkpointCards.innerHTML =
        "<p>Could not load flashcards from the backend. Is app.py running?</p>";
    }

    checkpointOverlay.classList.remove("hidden");
  }

  // -----------------------------
  // Build level
  // -----------------------------
  function buildLevel() {
    let checkpointCounter = 0;

    for (let row = 0; row < ROWS; row++) {
      const line = MAP[row];
      for (let col = 0; col < COLS; col++) {
        const ch = line[col];
        const x = col * TILE;
        const y = row * TILE;

        switch (ch) {
          case "W":
            game.walls.push(new Wall(x, y, TILE, TILE));
            break;
          case ".":
            game.pumpkins.push(new Pumpkin(x, y));
            break;
          case "P":
            game.player = new Player(x + TILE * 0.1, y + TILE * 0.1);
            break;
          case "E":
            game.enemy = new Enemy(x + TILE * 0.1, y + TILE * 0.1);
            break;
          case "F":
            game.family.push(new FamilyMember(x, y));
            break;
          case "C":
            game.checkpoints.push(
              new Checkpoint(x, y, 1, checkpointCounter++)
            );
            break;
          default:
            // empty space
            break;
        }
      }
    }

    if (!game.player) {
      game.player = new Player(TILE, TILE);
    }
  }

  // -----------------------------
  // Input handling
  // -----------------------------
  const keys = {};
  window.addEventListener("keydown", (e) => {
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
      keys[e.key] = true;
      e.preventDefault();
    }
  });
  window.addEventListener("keyup", (e) => {
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
      keys[e.key] = false;
      e.preventDefault();
    }
  });

  // -----------------------------
  // Update & draw
  // -----------------------------
  function update() {
    if (!game.running) return;

    if (game.player) {
      game.player.handleInput(keys);
    }
    if (game.enemy) {
      game.enemy.update();
    }

    // Pumpkins
    for (let i = game.pumpkins.length - 1; i >= 0; i--) {
      const p = game.pumpkins[i];
      if (p.intersects(game.player)) {
        game.points += p.points;
        game.pumpkins.splice(i, 1);
      }
    }

    // Family
    for (const fam of game.family) {
      if (!fam.collected && fam.intersects(game.player)) {
        fam.collected = true;
        const collected = game.family.filter(f => f.collected).length;
        const total = game.family.length;
        if (collected === total) {
          endGame("win");
        }
      }
    }

    // Checkpoints
    for (const cp of game.checkpoints) {
      if (!cp.triggered && cp.intersects(game.player)) {
        showCheckpoint(cp);
        break;
      }
    }
  }

  function drawGridBackground(ctx) {
    ctx.fillStyle = "#05020a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "#15152a";
    ctx.lineWidth = 1;
    for (let x = 0; x <= canvas.width; x += TILE) {
      ctx.beginPath();
      ctx.moveTo(x + 0.5, 0);
      ctx.lineTo(x + 0.5, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y <= canvas.height; y += TILE) {
      ctx.beginPath();
      ctx.moveTo(0, y + 0.5);
      ctx.lineTo(canvas.width, y + 0.5);
      ctx.stroke();
    }
  }

  function draw() {
    drawGridBackground(ctx);

    // Walls
    for (const w of game.walls) w.draw(ctx);
    // Pumpkins
    for (const p of game.pumpkins) p.draw(ctx);
    // Family
    for (const fam of game.family) fam.draw(ctx);
    // Checkpoints
    for (const cp of game.checkpoints) cp.draw(ctx);
    // Player / enemy
    if (game.player) game.player.draw(ctx);
    if (game.enemy) game.enemy.draw(ctx);

    // HUD
    ctx.fillStyle = "#ffffff";
    ctx.font = "12px 'Press Start 2P', monospace";
    ctx.fillText("Points: " + game.points, 16, 24);

    // Family bar at bottom
    let offsetIndex = 0;
    for (const fam of game.family) {
      if (fam.collected) {
        fam.drawCollectedIcon(ctx, offsetIndex);
        offsetIndex++;
      }
    }
  }

  function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
  }

  // -----------------------------
  // Init
  // -----------------------------
  buildLevel();
  loop();
})();
