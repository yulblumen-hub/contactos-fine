/* Contactos F!NE — arma la página a partir de window.FINE (data.js, generado por build.py). */

(function () {
  "use strict";

  var D = window.FINE;
  if (!D) return;

  var $ = function (id) { return document.getElementById(id); };

  var ICONOS = {
    contacto: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M4 20h16"/></svg>',
    whatsapp: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38a9.9 9.9 0 0 0 4.79 1.22h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.82 9.82 0 0 0 12.04 2Zm5.8 14.1c-.24.68-1.42 1.31-1.96 1.36-.5.05-.98.24-3.3-.69-2.78-1.1-4.55-3.94-4.69-4.12-.14-.19-1.13-1.5-1.13-2.86 0-1.36.71-2.03.96-2.31.25-.28.55-.35.73-.35.18 0 .37 0 .53.01.17.01.4-.06.62.48.24.57.8 1.97.87 2.11.07.14.12.31.02.5-.09.19-.14.31-.28.47-.14.16-.29.36-.42.48-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.07.95 1.97 1.25 2.25 1.39.28.14.44.12.6-.07.17-.19.7-.81.88-1.09.19-.28.37-.23.63-.14.25.09 1.65.78 1.93.92.28.14.47.21.54.33.07.11.07.66-.17 1.35Z"/></svg>',
    mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="m3 7 9 6 9-6"/></svg>'
  };

  function crear(tag, clase, texto) {
    var el = document.createElement(tag);
    if (clase) el.className = clase;
    if (texto) el.textContent = texto;
    return el;
  }

  function boton(clase, icono, texto, href, nuevaPestana) {
    var a = crear("a", "btn " + clase);
    a.href = href;
    a.innerHTML = icono + "<span></span>";
    a.lastChild.textContent = texto;
    if (nuevaPestana) {
      a.target = "_blank";
      a.rel = "noopener";
    }
    return a;
  }

  /* wa.me solo acepta digitos: sin +, espacios ni guiones. */
  function soloDigitos(tel) {
    return String(tel || "").replace(/\D/g, "");
  }

  function iniciales(nombre, apellido) {
    var a = (nombre || "").trim().charAt(0);
    var b = (apellido || "").trim().charAt(0);
    return (a + b).toUpperCase() || a.toUpperCase();
  }

  /* ---------------- Cabecera ---------------- */

  $("bajada").textContent = D.empresa.bajada;

  [
    { texto: "Web", url: D.empresa.web },
    { texto: "Mercado Libre", url: D.empresa.tienda },
    { texto: "Instagram", url: D.empresa.instagram }
  ].forEach(function (item) {
    if (!item.url) return;
    var a = crear("a", null, item.texto);
    a.href = item.url;
    a.target = "_blank";
    a.rel = "noopener";
    $("links").appendChild(a);
  });

  /* ---------------- Atajos ---------------- */

  (D.atajos || []).forEach(function (atajo) {
    var b = crear("button", "chip", atajo.texto);
    b.type = "button";
    b.addEventListener("click", function () {
      var destino = document.getElementById("area-" + atajo.area);
      if (!destino) return;
      destino.scrollIntoView({ block: "start" });
      destino.classList.add("area--destacada");
      setTimeout(function () { destino.classList.remove("area--destacada"); }, 2400);
    });
    $("atajos").appendChild(b);
  });

  /* ---------------- Tarjetas ---------------- */

  function tarjeta(persona) {
    var caja = crear("article", "tarjeta");
    var completo = (persona.nombre + " " + (persona.apellido || "")).trim();

    var fila = crear("div", "tarjeta__fila");
    fila.appendChild(crear("div", "avatar", iniciales(persona.nombre, persona.apellido)));

    var datos = crear("div");
    datos.appendChild(crear("h3", "tarjeta__nombre", completo));
    if (persona.cargo) datos.appendChild(crear("p", "tarjeta__cargo", persona.cargo));
    fila.appendChild(datos);
    caja.appendChild(fila);

    var acciones = crear("div", "tarjeta__acciones");
    var wa = soloDigitos(persona.whatsapp || persona.telefono);

    // WhatsApp primero: es la vía que más se usa y la que el visitante busca.
    if (wa) {
      acciones.appendChild(
        boton("btn--lima", ICONOS.whatsapp, "WhatsApp", "https://wa.me/" + wa, true)
      );
    }

    if (persona.mail) {
      acciones.appendChild(boton("", ICONOS.mail, "Mail", "mailto:" + persona.mail, false));
    }

    if (persona.mail || persona.telefono) {
      var guardar = boton("", ICONOS.contacto, "Guardar contacto", persona.vcf, false);
      // El nombre del archivo es lo que ve el usuario al descargarlo.
      guardar.setAttribute("download", completo + ".vcf");
      acciones.appendChild(guardar);
    }

    if (acciones.childNodes.length) {
      caja.appendChild(acciones);
    } else {
      caja.appendChild(crear("p", "pendiente", "Datos de contacto pendientes de carga."));
    }

    return caja;
  }

  var contenedor = $("areas");

  (D.areas || []).forEach(function (area, i) {
    var seccion = crear("section", "area aparece");
    seccion.id = "area-" + area.id;
    seccion.style.animationDelay = (0.05 + i * 0.06).toFixed(2) + "s";

    var cabecera = crear("div", "area__cabecera");
    cabecera.appendChild(crear("span", "area__indice", String(i + 1).padStart(2, "0")));
    cabecera.appendChild(crear("h2", "area__nombre", area.nombre));
    seccion.appendChild(cabecera);

    if (area.detalle) seccion.appendChild(crear("p", "area__detalle", area.detalle));
    (area.personas || []).forEach(function (persona) {
      seccion.appendChild(tarjeta(persona));
    });

    contenedor.appendChild(seccion);
  });

  /* ---------------- Cierre ---------------- */

  /* Contacto general: el comercial si tiene WhatsApp cargado, si no el primero que tenga. */
  function generalWhatsApp() {
    var candidatos = [];
    (D.areas || []).forEach(function (area) {
      (area.personas || []).forEach(function (persona) {
        var wa = soloDigitos(persona.whatsapp || persona.telefono);
        if (wa) candidatos.push({ area: area.id, wa: wa });
      });
    });
    var comercial = candidatos.filter(function (c) { return c.area === "comercial"; });
    return (comercial[0] || candidatos[0] || {}).wa || "";
  }

  var cierre = $("cierre-acciones");
  var general = generalWhatsApp();

  if (general) {
    cierre.appendChild(
      boton("btn--lima", ICONOS.whatsapp, "Escribinos por WhatsApp", "https://wa.me/" + general, true)
    );
  }

  if (D.empresa.mailGeneral) {
    cierre.appendChild(
      boton("", ICONOS.mail, D.empresa.mailGeneral, "mailto:" + D.empresa.mailGeneral, false)
    );
  }

  /* ---------------- Compartir ---------------- */

  if (navigator.share) {
    var compartir = $("compartir");
    compartir.hidden = false;
    compartir.addEventListener("click", function () {
      navigator.share({
        title: "Contactos · " + D.empresa.nombre,
        url: window.location.href
      }).catch(function () { /* cancelado por el usuario */ });
    });
  }
})();
