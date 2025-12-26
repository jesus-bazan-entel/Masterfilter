/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html", // Busca archivos HTML en la carpeta templates
    "./static/**/*.js", // Busca archivos JavaScript en la carpeta static
    "./static/**/*.vue", // Busca archivos Vue en la carpeta static
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
