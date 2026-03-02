// ===== บังคับให้ล็อกอินก่อนดูหน้าสินค้า (products / products-review) =====
(function checkLoginRequired() {
  if (document.body && document.body.classList.contains("products-page")) {
    if (!localStorage.getItem("champa_token")) {
      var next = (window.location.pathname || "") + (window.location.search || "") || "/brand/products.html";
      window.location.replace("/login?next=" + encodeURIComponent(next));
      return;
    }
  }
})();

// ===== ฝั่ง Client: แสดงปุ่มออกจากระบบเมื่อล็อกอินแล้ว =====
(function setupClientLogout() {
  function applyLogoutLink() {
    var link = document.querySelector(".header-login");
    if (!link) return;
    if (localStorage.getItem("champa_token")) {
      link.textContent = "ອອກຈາກລະບົບ";
      link.href = "#";
      link.removeEventListener("click", handleLogoutClick);
      link.addEventListener("click", handleLogoutClick);
    } else {
      link.textContent = "ເຂົ້າສູ່ລະບົບ";
      link.href = "/login";
      link.removeEventListener("click", handleLogoutClick);
    }
  }
  function handleLogoutClick(e) {
    e.preventDefault();
    var token = localStorage.getItem("champa_token");
    if (token) {
      fetch((window.location.origin || "") + "/api/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token }
      }).then(function () {
        localStorage.removeItem("champa_token");
        window.location.href = "/brand/";
      }).catch(function () {
        localStorage.removeItem("champa_token");
        window.location.href = "/brand/";
      });
    } else {
      window.location.href = "/brand/";
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyLogoutLink);
  } else {
    applyLogoutLink();
  }
  document.addEventListener("header-loaded", applyLogoutLink);
})();

// ===== NAV Mobile (รองรับทั้ง header ในหน้าและ header โหลดจาก partial) =====
function bindHeaderNav() {
  var hamburger = document.getElementById("hamburger");
  var menu = document.getElementById("menu");
  if (hamburger && menu && !hamburger._headerBound) {
    hamburger._headerBound = true;
    hamburger.addEventListener("click", function () {
      menu.classList.toggle("open");
    });
  }
}
bindHeaderNav();
document.addEventListener("header-loaded", bindHeaderNav);

// ===== Hero carousel (Finix-style) =====
let heroSlideIndex = 0;
let heroSlideTimer = null;
const heroSlides = document.getElementsByClassName("hero-slide");
const heroDotsEl = document.getElementById("heroDots");
const heroPrevBtn = document.getElementById("heroPrev");
const heroNextBtn = document.getElementById("heroNext");

function goToHeroSlide(n) {
  if (!heroSlides || heroSlides.length === 0) return;
  for (let i = 0; i < heroSlides.length; i++) {
    heroSlides[i].classList.remove("active");
  }
  if (n >= heroSlides.length) heroSlideIndex = 0;
  else if (n < 0) heroSlideIndex = heroSlides.length - 1;
  else heroSlideIndex = n;
  heroSlides[heroSlideIndex].classList.add("active");
  const dots = document.querySelectorAll("#heroDots .carousel-dot");
  dots.forEach((d, i) => d.classList.toggle("active", i === heroSlideIndex));
  if (heroSlideTimer) clearTimeout(heroSlideTimer);
  heroSlideTimer = setTimeout(() => goToHeroSlide(heroSlideIndex + 1), 3500);
}

if (heroSlides.length > 0 && heroDotsEl) {
  for (let i = 0; i < heroSlides.length; i++) {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "carousel-dot" + (i === 0 ? " active" : "");
    dot.setAttribute("aria-label", "ສະໄລທີ " + (i + 1));
    dot.addEventListener("click", () => goToHeroSlide(i));
    heroDotsEl.appendChild(dot);
  }
}
if (heroPrevBtn) heroPrevBtn.addEventListener("click", () => goToHeroSlide(heroSlideIndex - 1));
if (heroNextBtn) heroNextBtn.addEventListener("click", () => goToHeroSlide(heroSlideIndex + 1));
if (heroSlides && heroSlides.length > 0) goToHeroSlide(0);

// ===== Sample shirts carousel =====
const sampleTrack = document.getElementById("sampleTrack");
const samplePrev = document.getElementById("samplePrev");
const sampleNext = document.getElementById("sampleNext");
let sampleIndex = 0;
const sampleItems = document.querySelectorAll(".sample-item");
const sampleTotal = sampleItems.length;

function getSampleVisible() {
  if (window.innerWidth <= 560) return 1;
  if (window.innerWidth <= 900) return 2;
  return 3;
}

function updateSampleCarousel() {
  if (!sampleTrack || sampleItems.length === 0) return;
  const visible = getSampleVisible();
  const maxIndex = Math.max(0, sampleTotal - visible);
  sampleIndex = Math.min(Math.max(0, sampleIndex), maxIndex);
  const item = sampleItems[0];
  if (!item) return;
  const gap = 20;
  const step = item.offsetWidth + gap;
  sampleTrack.style.transform = "translateX(-" + sampleIndex * step + "px)";
}

if (sampleTrack && sampleItems.length > 0) {
  if (samplePrev) samplePrev.addEventListener("click", () => { sampleIndex = Math.max(0, sampleIndex - 1); updateSampleCarousel(); });
  if (sampleNext) sampleNext.addEventListener("click", () => { sampleIndex++; updateSampleCarousel(); });
  window.addEventListener("resize", updateSampleCarousel);
  updateSampleCarousel();
}

// ===== Footer Year =====
const yearEl = document.getElementById("year");
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ===== Products Data =====
const STORAGE_KEY = "champa_added_products";
const defaultProducts = [
  { id: 1, title: "Jersey Pro Blue", price: "LAK 199.000", type: "football", badge: "ຂາຍດີ", desc: "ເສື້ອບານເຕະພິມລາຍໂທນນ້ຳເງິນ-ຂາວ ໃສ່ສະບາຍ ເໝາະກັບທີມແຂ່ງ", image: "images/products/1.jpg" },
  { id: 2, title: "Runner Light White", price: "LAK 179.000", type: "running", badge: "ມາໃໝ່", desc: "ເສື້ອວິ່ງຜ້າເບົາ ລະບາຍອາກາດດີ ເໝາະກັບງານວິ່ງແລະຊ້ອມ", image: "images/products/2.jpg" },
  { id: 3, title: "Basket Pro Storm", price: "LAK 229.000", type: "basketball", badge: "ຂາຍດີ", desc: "ເສື້ອບາສດີໄຊນ໌ດຸດັນ ໂທນສະປອດ ງານພິມຄົມຊັດ", image: "images/products/3.jpg" },
  { id: 4, title: "eSport Neon Blue", price: "LAK 259.000", type: "esport", badge: "HOT", desc: "ເສື້ອ eSport ດີໄຊນ໌ລ້ຳ ເທ່ແບບທີມແຂ່ງ ພ້ອມໃສ່ໂລໂກ້ສະປອນເຊີ", image: "images/products/4.jpg" },
  { id: 5, title: "Football Classic White", price: "LAK 189.000", type: "football", badge: "Classic", desc: "ເສື້ອບານເຕະໂທນຂາວສະອາດ ໃສ່ງ່າຍ ເບິ່ງມືອາຊີບ", image: "images/products/5.jpg" },
  { id: 6, title: "Runner Pro Blue Wave", price: "LAK 199.000", type: "running", badge: "New", desc: "ເສື້ອວິ່ງລາຍຄື່ນນ້ຳເງິນ ດ້ອດເດັ່ນ ຖ່າຍຮູບສວຍ", image: "images/products/6.jpg" }
];

// สินค้าจาก API (เมื่อเปิดผ่าน Flask จะโหลดจาก /api/products)
let apiProducts = [];

let addedProducts = [];
try {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) addedProducts = JSON.parse(saved);
} catch (_) {}

function getAllProducts() {
  // เมื่อมีสินค้าจาก API (เพิ่มจาก Admin) ใช้เป็นรายการหลัก ไม่ปนกับของคงที่ เพื่อให้สินค้าจาก Admin แสดงใน Client
  if (apiProducts.length > 0) {
    return [...apiProducts, ...addedProducts];
  }
  return [...defaultProducts, ...addedProducts];
}

// ===== Render Products =====
const grid = document.getElementById("productGrid");
function renderProducts(list) {
  if (!grid) return;
  grid.innerHTML = "";

  list.forEach((p) => {
    const card = document.createElement("div");
    card.className = "product";
    const thumbContent = p.image
      ? `<img src="${p.image}" alt="${p.title}" class="thumb-img" onerror="this.style.display='none'" /><div class="badge">${p.badge || ""}</div>`
      : `<div class="badge">${p.badge || ""}</div>`;
    card.innerHTML = `
      <div class="thumb">
        ${thumbContent}
      </div>
      <div class="product-title">${p.title}</div>
      <div class="muted">${typeLabel(p.type)}</div>
      <div class="product-actions">
        <div class="price">${p.price}</div>
        <button class="btn small primary" data-buy="${p.id}">ສັ່ງຊື້</button>
      </div>
    `;
    grid.appendChild(card);
  });

  document.querySelectorAll("[data-buy]").forEach((btn) => {
    btn.addEventListener("click", () => openModal(+btn.dataset.buy));
  });
}

function typeLabel(type) {
  const map = {
    football: "ເສື້ອບານເຕະ",
    running: "ເສື້ອວິ່ງ",
    basketball: "ເສື້ອບາສ",
    esport: "ເສື້ອ eSport"
  };
  return map[type] || "ເສື້ອກິລາ";
}

// Category for products page filter: all | company | agency | event | sport | jersey
function getProductCategory(type) {
  const map = {
    football: "jersey",
    running: "event",
    basketball: "agency",
    esport: "sport"
  };
  return map[type] || "sport";
}

// แปลง category เป็นข้อความแสดง (ตามที่เลือกตอนเพิ่ม)
function getCategoryLabel(category) {
  const map = {
    company: "ເສື້ອບານເຕະ",
    agency: "ເສື້ອຕີບານ",
    event: "ເສື້ອແລ່ນ",
    sport: "ເສື້ອ E-Sport",
    jersey: "ເສື້ອ ທີມງານ"
  };
  return map[category] || category || "";
}

// ===== Render Products ===== (work-style cards on products page)
var PRODUCTS_INITIAL = 10; // แสดง 10 รายการก่อน แล้วค่อยดูเพิ่ม

function renderProducts(list) {
  if (!grid) return;
  grid.innerHTML = "";
  const isWorkGrid = grid.classList.contains("products-grid-work");
  const contactHtml = '';

  // หน้าสินค้า: แสดง 10 รายการก่อน ถ้ามากกว่านั้นมีปุ่มดูเพิ่ม
  var showAll = grid.hasAttribute("data-show-all");
  var listToShow = list;
  if (isWorkGrid && list.length > PRODUCTS_INITIAL && !showAll) {
    listToShow = list.slice(0, PRODUCTS_INITIAL);
  }

  listToShow.forEach((p) => {
    const card = document.createElement("div");
    if (isWorkGrid) {
      const imgSrc = p.image || "";
      const imgTag = imgSrc ? `<img src="${imgSrc}" alt="${p.title}" onerror="this.style.display='none'" />` : "";
      const freeTag = (p.badge && (p.badge === "FREE" || p.badge === "ຟຣີ")) ? '<span class="product-card-free">FREE</span>' : "";
      const categoryLabel = getCategoryLabel(p.category || getProductCategory(p.type));
      const collarLabel = p.price_type || "";
      const descShort = (p.desc || "").length > 60 ? (p.desc || "").slice(0, 60) + "…" : (p.desc || "");
      card.className = "product-card-work";
      card.innerHTML = `
        <div class="product-card-images">
          <div class="product-card-img product-card-img-single">${imgTag}${freeTag}</div>
        </div>
        <div class="product-card-body">
          <div class="product-card-brand">${p.title}</div>
          ${categoryLabel ? '<div class="product-card-category muted">' + categoryLabel + '</div>' : ''}
          ${collarLabel ? '<div class="product-card-collar muted">' + collarLabel + '</div>' : ''}
          ${descShort ? '<div class="product-card-desc muted">' + descShort + '</div>' : ''}
        </div>
        <div class="product-card-actions">
          <button type="button" class="btn small primary" data-buy="${p.id}">ສັ່ງຊື້</button>
        </div>
      `;
    } else {
      card.className = "product";
      const thumbContent = p.image
        ? `<img src="${p.image}" alt="${p.title}" class="thumb-img" onerror="this.style.display='none'" /><div class="badge">${p.badge || ""}</div>`
        : `<div class="badge">${p.badge || ""}</div>`;
      const categoryLabel = getCategoryLabel(p.category || getProductCategory(p.type));
      card.innerHTML = `
        <div class="thumb">${thumbContent}</div>
        <div class="product-title">${p.title}</div>
        <div class="muted">${categoryLabel || typeLabel(p.type)}</div>
        <div class="product-actions">
          <button class="btn small primary" data-buy="${p.id}">ສັ່ງຊື້</button>
        </div>
      `;
    }
    grid.appendChild(card);
  });

  if (isWorkGrid && list.length > PRODUCTS_INITIAL && !showAll) {
    var wrap = document.createElement("div");
    wrap.className = "products-load-more-wrap";
    wrap.style.gridColumn = "1 / -1";
    wrap.innerHTML = '<button type="button" class="btn ghost products-load-more" id="productsLoadMore">ເບິ່ງເພີ່ມ (' + (list.length - PRODUCTS_INITIAL) + ' ລາຍການ)</button>';
    grid.appendChild(wrap);
    var loadBtn = document.getElementById("productsLoadMore");
    if (loadBtn) {
      loadBtn.addEventListener("click", function () {
        grid.setAttribute("data-show-all", "true");
        renderProducts(list);
      });
    }
  }

  grid.querySelectorAll("[data-buy]").forEach((btn) => {
    btn.addEventListener("click", () => openModal(+btn.dataset.buy));
  });
}

// ===== Filter (chips on old layout / products-tab on products page) =====
const chips = document.querySelectorAll(".chip");
const productsTabs = document.querySelectorAll(".products-tab");

function applyFilter() {
  let f = "all";
  const activeTab = document.querySelector(".products-tab.active");
  const activeChip = document.querySelector(".chip.active");
  if (activeTab) f = activeTab.dataset.filter || "all";
  else if (activeChip) f = activeChip.dataset.filter || "all";

  if (grid) grid.removeAttribute("data-show-all");
  const list = f === "all"
    ? getAllProducts()
    : getAllProducts().filter((p) => {
        // ใช้ category จาก product โดยตรง (komon, kovi, ko5lien, kopo)
        // ถ้าไม่มี category ให้ fallback ไปใช้ getProductCategory(p.type) สำหรับสินค้าเก่า
        const category = p.category || getProductCategory(p.type);
        return category === f;
      });
  renderProducts(list);
}

chips.forEach((c) => {
  c.addEventListener("click", () => {
    chips.forEach((x) => x.classList.remove("active"));
    c.classList.add("active");
    applyFilter();
  });
});
productsTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    productsTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    applyFilter();
  });
});

// ===== หน้ารายการสินค้า: ช่องค้นหา + เลือกประเภทคอ (ຄໍມົນ, ຄໍວີ-ວີໄຂວ, ຄໍ5ລ່ຽນ, ຄໍໂປໂລ) =====
(function setupProductsSearch() {
  var searchBtn = document.getElementById("productsSearchBtn");
  var searchInput = document.getElementById("productsSearchInput");
  var collarSelect = document.getElementById("productsCollarSelect");
  var productsTabsList = document.querySelectorAll(".products-tab");
  if (!searchBtn || !searchInput) return;

  function doSearch() {
    var searchTerm = searchInput.value.trim().toLowerCase();
    var collarType = collarSelect ? collarSelect.value : "";
    var list = getAllProducts();
    if (searchTerm) {
      list = list.filter(function (p) {
        var title = (p.title || "").toLowerCase();
        return title.indexOf(searchTerm) !== -1;
      });
    }
    if (collarType) {
      list = list.filter(function (p) {
        var collar = (p.price_type || "").trim();
        return collar === collarType;
      });
    }
    if (typeof renderProducts === "function") renderProducts(list);
    if (grid) grid.removeAttribute("data-show-all");
    var tabToActivate = null;
    if (productsTabsList.length) {
      for (var i = 0; i < productsTabsList.length; i++) {
        if (productsTabsList[i].dataset.filter === (collarType || "all")) {
          tabToActivate = productsTabsList[i];
          break;
        }
      }
      if (!tabToActivate && !collarType) tabToActivate = document.querySelector('.products-tab[data-filter="all"]');
      if (tabToActivate) {
        for (var j = 0; j < productsTabsList.length; j++) productsTabsList[j].classList.remove("active");
        tabToActivate.classList.add("active");
      }
    }
  }

  searchBtn.addEventListener("click", doSearch);
  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      searchBtn.click();
    }
  });
  document.addEventListener("productsSearch", function (e) {
    var d = e.detail || {};
    if (d.search !== undefined && searchInput) searchInput.value = d.search || "";
    if (d.collar !== undefined && collarSelect) collarSelect.value = d.collar || "";
    doSearch();
  });
})();

// เปิดแท็บตาม ?filter= จากลิงก์ (เช่น index หมวดหมู่ → products.html?filter=jersey)
var hash = window.location.search;
var filterMatch = hash && hash.match(/[?&]filter=([^&]+)/);
if (filterMatch && productsTabs.length) {
  var wantFilter = filterMatch[1];
  var tab = Array.from(productsTabs).find(function (t) { return t.dataset.filter === wantFilter; });
  if (tab) {
    productsTabs.forEach(function (t) { t.classList.remove("active"); });
    tab.classList.add("active");
  }
}

// โหลดสินค้าจาก API (เมื่อรันผ่าน Flask)
(async function initProducts() {
  try {
    const r = await fetch("/api/products");
    if (r.ok) {
      const data = await r.json();
      apiProducts = data.map(function (p) {
        var imgUrl = p.image ? (p.image.indexOf("/") === 0 ? p.image : "/static/" + p.image) : "";
        return {
          id: p.id,
          title: p.name,
          type: "football",
          badge: p.stock > 0 ? "ມີສິນຄ້າ" : "ໝົດ",
          desc: p.description || "",
          category: p.category || "",
          price_type: p.price_type || "",
          image: imgUrl
        };
      });
      
      // แสดงสินค้าในหน้าหลัก (homepage)
      renderHomeProducts(apiProducts);
    }
  } catch (e) {}
  if (grid) applyFilter();
})();

// ===== Trust Review (หน้า index): โหลดรีวิวจาก API /api/reviews + รูปจาก product ที่ตรงกับ product_id =====
(async function loadTrustReviews() {
  const listEl = document.getElementById("trustReviewList");
  const moreLink = document.getElementById("trustReviewMore");
  if (!listEl) return;
  try {
    const [reviewsRes, productsRes] = await Promise.all([
      fetch("/api/reviews"),
      fetch("/api/products")
    ]);
    if (!reviewsRes.ok) return;
    const reviews = await reviewsRes.json();
    const products = productsRes.ok ? await productsRes.json() : [];
    const showCount = 3;
    const slice = (reviews || []).slice(0, showCount);
    if (slice.length === 0) {
      listEl.innerHTML = '<p class="trust-review-empty muted">ຍັງບໍ່ມີລີວິວ</p>';
      return;
    }
    listEl.innerHTML = slice.map(function (rev) {
      const product = rev.product_id != null ? products.find(function (p) { return p.id === rev.product_id; }) : null;
      const stars = "⭐".repeat(Math.min(5, Math.max(0, rev.rating || 0)));
      const name = (rev.customer_name || "ລູກຄ້າ").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      // เนื้อหา: ใช้จาก product.description ก่อน ถ้าไม่มีใช้ comment รีวิว
      let content = "";
      if (product && product.description) {
        content = (product.description || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      } else {
        content = (rev.comment || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      }
      const shortContent = content.length > 120 ? content.slice(0, 120) + "…" : content;
      // รูป: ใช้จาก review.images ก่อน ถ้าไม่มีให้ดึงจาก product ที่ product_id ตรงกับ review
      let imgSrc = "";
      if (rev.images && rev.images.length > 0) {
        imgSrc = rev.images[0].indexOf("/") === 0 ? rev.images[0] : "/static/" + rev.images[0];
      } else if (product && product.image) {
        imgSrc = product.image.indexOf("/") === 0 ? product.image : "/static/" + product.image;
      }
      const imgTag = imgSrc
        ? '<div class="trust-review-thumb"><a href="products-review.html" class="trust-review-thumb-link" aria-label="ເບິ່ງລີວິວທັງໝົດ"><img src="' + imgSrc + '" alt="" onerror="this.parentElement.style.display=\'none\'" /></a></div>'
        : "";
      const productName = product && product.name ? (product.name + "").replace(/</g, "&lt;").replace(/>/g, "&gt;") : "";
      const productTitleHtml = productName ? '<div class="trust-review-product">' + productName + '</div>' : "";
      return (
        '<div class="trust-review-item">' +
        imgTag +
        '<div class="trust-review-body">' +
        productTitleHtml +
        '<div class="trust-review-stars">' + stars + '</div>' +
        (shortContent ? '<p class="trust-review-comment">' + shortContent + '</p>' : '') +
        '</div></div>'
      );
    }).join("");
    if (moreLink) moreLink.style.display = reviews.length > 0 ? "inline-block" : "none";
  } catch (e) {
    listEl.innerHTML = '<p class="trust-review-empty muted">ບໍ່ສາມາດໂຫຼດລີວິວໄດ້</p>';
  }
})();

// แสดงสินค้าในหน้าหลัก (แสดงแค่ประเภทและเนื้อหา)
function renderHomeProducts(products) {
  const homeGrid = document.getElementById("homeProductsGrid");
  const showcaseSection = document.getElementById("productsShowcaseSection");
  if (!homeGrid || !showcaseSection) return;
  
  if (products.length === 0) {
    showcaseSection.style.display = "none";
    return;
  }
  
  showcaseSection.style.display = "block";
  homeGrid.innerHTML = "";
  
  products.forEach((p) => {
    const card = document.createElement("div");
    card.className = "product-card-work";
    const imgSrc = p.image || "";
    const imgTag = imgSrc ? `<img src="${imgSrc}" alt="${p.title}" onerror="this.style.display='none'" />` : "";
    
    // แสดง category, description และขนาดสินค้า
    // แปลง "jersey" เป็น "JERSEY" (ตัวใหญ่) และแสดง category เป็นสีฟ้า
    let displayCategory = p.category || "";
    if (displayCategory.toLowerCase() === "jersey") {
      displayCategory = "JERSEY";
    }
    const categoryHtml = displayCategory ? `<div class="product-card-category">${displayCategory}</div>` : "";
    const descHtml = p.desc ? `<div class="product-card-desc">${p.desc}</div>` : "";
    // แสดงขนาดสินค้า (XS S M L XL 2XL 3XL)
    const sizesHtml = `<div class="product-card-sizes">XS S M L XL 2XL 3XL</div>`;
    
    card.innerHTML = `
      <div class="product-card-images">
        <div class="product-card-img product-card-img-single">${imgTag}</div>
      </div>
      <div class="product-card-body">
        ${categoryHtml}
        ${descHtml}
        ${sizesHtml}
      </div>
    `;
    homeGrid.appendChild(card);
  });
}

// ===== Modal =====
const modal = document.getElementById("modal");
const closeModalBtn = document.getElementById("closeModal");
const modalBackdrop = document.getElementById("modalBackdrop");

const mTitle = document.getElementById("mTitle");
const mDesc = document.getElementById("mDesc");
const mType = document.getElementById("mType");
const mCollar = document.getElementById("mCollar");
const mPreview = document.getElementById("mPreview");
const copyTextBtn = document.getElementById("copyText");

function openModal(id) {
  if (!modal) return;
  var token = localStorage.getItem("champa_token");
  if (!token) {
    var next = encodeURIComponent(window.location.pathname + window.location.search || "/brand/products.html");
    window.location.href = "/login?next=" + next;
    return;
  }
  const p = getAllProducts().find((x) => x.id === id);
  if (!p) return;

  if (mTitle) mTitle.textContent = p.title;
  if (mDesc) mDesc.textContent = p.desc || "";
  if (mType) mType.textContent = getCategoryLabel(p.category || getProductCategory(p.type)) || "-";
  if (mCollar) mCollar.textContent = p.price_type || "-";

  if (mPreview) {
    if (p.image) {
      mPreview.style.background = "none";
      mPreview.style.backgroundImage = `url(${p.image})`;
      mPreview.style.backgroundSize = "cover";
      mPreview.style.backgroundPosition = "center";
    } else {
      mPreview.style.backgroundImage = "none";
      mPreview.style.background = `radial-gradient(500px 220px at 30% 30%, rgb(255, 255, 255), transparent 60%),
        linear-gradient(135deg, rgb(255, 255, 255), rgb(255, 255, 255))`;
      mPreview.style.backgroundSize = "";
      mPreview.style.backgroundPosition = "";
    }
  }

  modal.classList.add("show");
}

function closeModal() {
  if (!modal) return;
  modal.classList.remove("show");
}

if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
if (modalBackdrop) modalBackdrop.addEventListener("click", closeModal);

if (copyTextBtn && mTitle) {
  copyTextBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(mTitle.textContent);
      copyTextBtn.textContent = "ຄັດລອກແລ້ວ ✓";
      setTimeout(() => (copyTextBtn.textContent = "ຄັດລອກຊື່ສິນຄ້າ"), 1200);
    } catch (e) {
      alert("ຄັດລອກບໍ່ສຳເລັດ");
    }
  });
}

// ===== Add Product Form =====
const addProductWrap = document.getElementById("addProductWrap");
const btnToggleAddProduct = document.getElementById("btnToggleAddProduct");
const addProductForm = document.getElementById("addProductForm");
const addProductImage = document.getElementById("addProductImage");
const addProductImageBox = document.getElementById("addProductImageBox");
const addProductImagePlaceholder = document.getElementById("addProductImagePlaceholder");
const addProductImagePreview = document.getElementById("addProductImagePreview");
const btnCancelAddProduct = document.getElementById("btnCancelAddProduct");
const addProductResult = document.getElementById("addProductResult");

let addProductImageData = null;

function resetAddProductImage() {
  addProductImageData = null;
  if (addProductImage) addProductImage.value = "";
  if (addProductImagePreview) {
    addProductImagePreview.innerHTML = "";
    addProductImagePreview.hidden = true;
  }
  if (addProductImagePlaceholder) addProductImagePlaceholder.hidden = false;
}

if (btnToggleAddProduct && addProductWrap) {
  btnToggleAddProduct.addEventListener("click", () => {
    const isHidden = addProductWrap.hidden;
    addProductWrap.hidden = !isHidden;
    if (isHidden) {
      addProductForm.reset();
      resetAddProductImage();
      if (addProductResult) addProductResult.textContent = "";
    }
  });
}

if (btnCancelAddProduct && addProductWrap) {
  btnCancelAddProduct.addEventListener("click", () => {
    addProductWrap.hidden = true;
    addProductForm.reset();
    resetAddProductImage();
  });
}

if (addProductImageBox && addProductImage) {
  addProductImageBox.addEventListener("click", (e) => {
    if (e.target.closest(".remove-preview")) return;
    addProductImage.click();
  });
}

if (addProductImage && addProductImagePreview && addProductImagePlaceholder) {
  addProductImage.addEventListener("change", () => {
    const file = addProductImage.files && addProductImage.files[0];
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      addProductImageData = e.target.result;
      addProductImagePreview.innerHTML = `<img src="${addProductImageData}" alt="" /><button type="button" class="remove-preview" aria-label="Remove">×</button>`;
      const removeBtn = addProductImagePreview.querySelector(".remove-preview");
      if (removeBtn) {
        removeBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          resetAddProductImage();
        });
      }
      addProductImagePlaceholder.hidden = true;
      addProductImagePreview.hidden = false;
    };
    reader.readAsDataURL(file);
  });
}

if (addProductForm) {
  addProductForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const title = document.getElementById("addTitle").value.trim();
    const price = document.getElementById("addPrice").value.trim();
    const type = document.getElementById("addType").value;
    const category = type || "";
    const badge = document.getElementById("addBadge").value.trim() || "New";
    const desc = document.getElementById("addDesc").value.trim() || "-";
    if (!title || !price) return;

    const maxId = Math.max(0, ...defaultProducts.map((p) => p.id), ...addedProducts.map((p) => p.id));
    const newProduct = {
      id: maxId + 1,
      title,
      price,
      type: type || "football",
      category: category,
      badge,
      desc,
      image: addProductImageData || undefined
    };
    addedProducts.push(newProduct);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(addedProducts));
    } catch (err) {}

    if (addProductResult) addProductResult.textContent = "ເພີ່ມສິນຄ້າແລ້ວ!";
    addProductForm.reset();
    resetAddProductImage();

    applyFilter();
    addProductWrap.hidden = true;
  });
}

// ===== Contact Form =====
const contactForm = document.getElementById("contactForm");
const formResult = document.getElementById("formResult");
const formImages = document.getElementById("formImages");
const contactImageBox = document.getElementById("contactImageBox");
const contactImagePlaceholder = document.getElementById("contactImagePlaceholder");
const imagePreviewList = document.getElementById("imagePreviewList");

function resetContactImage() {
  if (formImages) formImages.value = "";
  if (imagePreviewList) {
    imagePreviewList.innerHTML = "";
    imagePreviewList.hidden = true;
  }
  if (contactImagePlaceholder) contactImagePlaceholder.hidden = false;
}

if (contactImageBox && formImages) {
  contactImageBox.addEventListener("click", (e) => {
    if (e.target.closest(".remove-preview")) return;
    formImages.click();
  });
}

if (formImages && imagePreviewList && contactImagePlaceholder) {
  formImages.addEventListener("change", () => {
    const file = formImages.files && formImages.files[0];
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreviewList.innerHTML = `<img src="${e.target.result}" alt="" /><button type="button" class="remove-preview" aria-label="Remove">×</button>`;
      const removeBtn = imagePreviewList.querySelector(".remove-preview");
      if (removeBtn) {
        removeBtn.addEventListener("click", (ev) => {
          ev.stopPropagation();
          resetContactImage();
        });
      }
      contactImagePlaceholder.hidden = true;
      imagePreviewList.hidden = false;
    };
    reader.readAsDataURL(file);
  });
}

if (contactForm) {
  contactForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const message = document.getElementById("message").value.trim();

    if (!name || !phone || !message) return;

    const hasImage = formImages && formImages.files && formImages.files.length > 0;
    const msg = hasImage
      ? "ສົ່ງຂໍ້ຄວາມສຳເລັດ! ເລືອກຮູບແລ້ວ (ຕົວຢ່າງລະບົບ) — ກະລຸນາຕິດຕໍ່ຜ່ານ FB/TikTok/ເບີໄດ້ເລີຍ"
      : "ສົ່ງຂໍ້ຄວາມສຳເລັດ! (ຕົວຢ່າງລະບົບ) — ກະລຸນາຕິດຕໍ່ຜ່ານ FB/TikTok/ເບີໄດ້ເລີຍ";
    formResult.textContent = msg;
    contactForm.reset();
    resetContactImage();
  });
}

// ===== Lightbox – กดดูรูปขยายได้ทุกหน้าที่มีรูป =====
(function () {
  var overlay = document.createElement("div");
  overlay.id = "imgLightbox";
  overlay.className = "lightbox-overlay";
  overlay.setAttribute("aria-hidden", "true");
  overlay.innerHTML = '<button type="button" class="lightbox-close" aria-label="ປິດ">✕</button><div class="lightbox-inner"><img src="" alt="" class="lightbox-img" /></div>';
  document.body.appendChild(overlay);

  var lbImg = overlay.querySelector(".lightbox-img");
  var lbClose = overlay.querySelector(".lightbox-close");

  function openLightbox(src, alt) {
    if (!lbImg || !overlay) return;
    lbImg.src = src;
    lbImg.alt = alt || "";
    overlay.classList.add("lightbox-open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    if (!overlay) return;
    overlay.classList.remove("lightbox-open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
  }

  if (overlay && lbClose) {
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay || e.target === lbClose) closeLightbox();
    });
  }
  if (lbImg) {
    lbImg.addEventListener("click", function (e) { e.stopPropagation(); });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && overlay && overlay.classList.contains("lightbox-open")) closeLightbox();
  });

  document.addEventListener("click", function (e) {
    var img = e.target.closest("img");
    if (!img || !img.src) return;
    if (img.closest(".nav, .header, .add-product-wrap, .add-image-box, .modal, .footer, .lightbox-overlay")) return;
    if (!document.body.classList.contains("products-page")) return;
    e.preventDefault();
    e.stopPropagation();
    openLightbox(img.currentSrc || img.src, img.alt || "");
  });
})();

// ===== Search ทั่วเว็บ (ຄົ້ນຫາ) =====
(function () {
  function initSiteSearch() {
    var input = document.getElementById("siteSearchInput");
    var resultsEl = document.getElementById("siteSearchResults");
    if (!input || !resultsEl || input._searchBound) return;
    input._searchBound = true;

    var pages = [
    { title: "ຫນ້າຫຼັກ", url: "index.html", label: "ໜ້າ" },
    { title: "ສິນຄ້າ", url: "products.html", label: "ໜ້າ" },
    { title: "ສິນຄ້າລີວິວ", url: "products-review.html", label: "ໜ້າ" },
    { title: "ຕິດຕໍ່", url: "contact.html", label: "ໜ້າ" },
    { title: "ຜົນງານ", url: "products.html", label: "ໜ້າສິນຄ້າ" },
    { title: "ອອກແບບເສື້ອ", url: "products.html", label: "ໜ້າສິນຄ້າ" }
  ];

  function getSearchIndex() {
    var items = pages.slice();
    try {
      var products = typeof getAllProducts === "function" ? getAllProducts() : [];
      products.forEach(function (p) {
        items.push({ title: p.title, url: "products.html?search=" + encodeURIComponent(p.title), label: "ສິນຄ້າ" });
      });
    } catch (e) {}
    return items;
  }

  function showResults(q) {
    q = (q || "").trim().toLowerCase();
    if (q.length < 1) {
      resultsEl.hidden = true;
      resultsEl.innerHTML = "";
      return;
    }
    var index = getSearchIndex();
    var matched = index.filter(function (item) {
      return item.title.toLowerCase().indexOf(q) !== -1;
    });
    resultsEl.innerHTML = matched.slice(0, 10).map(function (item) {
      return '<a href="' + item.url + '" class="search-result-item"><span class="search-result-title">' + escapeHtml(item.title) + '</span><span class="search-result-label">' + escapeHtml(item.label) + '</span></a>';
    }).join("");
    resultsEl.hidden = matched.length === 0;
  }

  function escapeHtml(s) {
    var div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  var timer;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { showResults(input.value); }, 150);
  });
  input.addEventListener("focus", function () { showResults(input.value); });
  input.addEventListener("blur", function () {
    setTimeout(function () { resultsEl.hidden = true; }, 200);
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest("#headerSearchWrap")) resultsEl.hidden = true;
  });
  }
  initSiteSearch();
  document.addEventListener("header-loaded", initSiteSearch);
})();

// ໜ້າສິນຄ້າ: ຖ້າມີ ?search= ໃນ URL ໃຫ້ກອງສິນຄ້າຕາມຄຳຄົ້ນຫາ
(function () {
  var grid = document.getElementById("productGrid");
  if (!grid) return;
  var match = window.location.search.match(/[?&]search=([^&]+)/);
  if (!match) return;
  var term = decodeURIComponent(match[1].replace(/\+/g, " ")).trim().toLowerCase();
  if (term.length < 1) return;
  try {
    var list = getAllProducts().filter(function (p) {
      return p.title.toLowerCase().indexOf(term) !== -1;
    });
    grid.setAttribute("data-show-all", "true");
    renderProducts(list);
  } catch (e) {}
})();

// ===== Header WhatsApp: dropdown เลือกเบอร์ =====
(function setupHeaderWhatsAppDropdown() {
  var headerWaLinks = document.querySelectorAll(".header-contact a[aria-label='WhatsApp']");
  if (!headerWaLinks.length) return;

  var numbers = [
    { label: "WhatsApp 1: +85620 12345678", href: "https://wa.me/8562012345678" },
    { label: "WhatsApp 2: +85620 78797726", href: "https://wa.me/8562078797726" }
  ];

  var currentOpen = null;

  headerWaLinks.forEach(function (link) {
    link.style.position = "relative";

    var menu = document.createElement("div");
    menu.className = "wa-dropdown";

    numbers.forEach(function (n) {
      var a = document.createElement("a");
      a.href = n.href;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = n.label;
      a.addEventListener("click", function () {
        // ปิด dropdown หลังจากเลือกเบอร์
        menu.classList.remove("open");
        currentOpen = null;
      });
      menu.appendChild(a);
    });

    link.appendChild(menu);
    link._waDropdown = menu;

    link.addEventListener("click", function (e) {
      e.preventDefault();
      // toggle dropdown
      if (currentOpen && currentOpen !== menu) {
        currentOpen.classList.remove("open");
      }
      var isOpen = menu.classList.toggle("open");
      currentOpen = isOpen ? menu : null;
    });
  });

  document.addEventListener("click", function (e) {
    if (!currentOpen) return;
    if (!e.target.closest(".header-contact a[aria-label='WhatsApp']")) {
      currentOpen.classList.remove("open");
      currentOpen = null;
    }
  });
})();