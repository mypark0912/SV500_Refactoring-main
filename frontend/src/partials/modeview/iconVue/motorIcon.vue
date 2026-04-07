<template>
  <svg viewBox="0 0 512 320" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="gBody" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#F7FBFF"/>
      <stop offset="1" stop-color="#B9D9F2"/>
    </linearGradient>
    <linearGradient id="gMid" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#EAF5FC"/>
      <stop offset="1" stop-color="#C8E2F5"/>
    </linearGradient>
    <linearGradient id="gDark" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#CDE6F6"/>
      <stop offset="1" stop-color="#9CC7E7"/>
    </linearGradient>
    <style>
      .s{stroke:#6C93BF;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
      .thin{stroke:#8FB5D3;stroke-width:3;stroke-linecap:round}
    </style>
  </defs>

  <rect x="18" y="282" width="482" height="28" rx="3" fill="url(#gBody)" class="s"/>
  <line x1="154" y1="282" x2="154" y2="310" class="s"/>

  <path d="M73 282C77 264 82 254 92 246H144C132 255 126 265 124 282H73Z" fill="url(#gDark)" class="s"/>
  <path d="M267 282C280 256 296 247 318 245H367C355 255 350 265 349 282H267Z" fill="url(#gDark)" class="s"/>

  <rect x="330" y="72" width="140" height="168" rx="56" fill="url(#gMid)" class="s"/>

  <rect x="196" y="76" width="168" height="156" rx="14" fill="url(#gMid)" class="s"/>
  <path d="M206 92H356L333 114H221L206 92Z" fill="#D8EDF9" class="s"/>

  <g class="thin">
    <line x1="214" y1="118" x2="356" y2="118"/>
    <line x1="210" y1="134" x2="356" y2="134"/>
    <line x1="208" y1="150" x2="356" y2="150"/>
    <line x1="206" y1="166" x2="356" y2="166"/>
    <line x1="206" y1="182" x2="356" y2="182"/>
    <line x1="206" y1="198" x2="354" y2="198"/>
    <line x1="208" y1="214" x2="350" y2="214"/>
  </g>

  <rect x="186" y="28" width="168" height="22" rx="3" fill="url(#gBody)" class="s"/>
  <rect x="205" y="10" width="50" height="18" rx="2" fill="url(#gMid)" class="s"/>
  <rect x="276" y="10" width="54" height="18" rx="2" fill="url(#gMid)" class="s"/>
  <rect x="204" y="50" width="146" height="32" fill="url(#gBody)" class="s"/>

  <circle cx="118" cy="160" r="98" fill="url(#gBody)" class="s"/>
  <ellipse cx="118" cy="160" rx="64" ry="74" fill="#F8FCFF" class="s"/>
  <circle cx="118" cy="160" r="44" fill="url(#gBody)" class="s"/>
  <path d="M83 160H28" class="s"/>
  <ellipse cx="24" cy="160" rx="20" ry="24" fill="url(#gMid)" class="s"/>
  <rect x="14" y="136" width="85" height="48" rx="22" fill="url(#gMid)" class="s"/>

  <g class="s">
    <line x1="118" y1="110" x2="118" y2="86"/>
    <line x1="118" y1="234" x2="118" y2="210"/>
    <line x1="67" y1="160" x2="44" y2="160"/>
    <line x1="169" y1="160" x2="191" y2="160"/>
  </g>
  <g class="thin">
    <line x1="70" y1="103" x2="62" y2="111"/>
    <line x1="167" y1="103" x2="175" y2="111"/>
    <line x1="70" y1="217" x2="62" y2="209"/>
    <line x1="167" y1="217" x2="175" y2="209"/>
  </g>

  <rect x="20" y="184" width="450" height="28" fill="#A8D2EE" opacity="0.45"/>
</svg>
</template>

<script setup>
</script>
