# Frontières de contexte

`useContext` est un Hook React. L'appeler uniquement au premier niveau d'un
composant fonction ou hook personnalisé, jamais conditionnellement ni dans un handler.

Context est résolu depuis le provider correspondant le plus proche au-dessus du
consommateur. Un provider retourné par le même composant ne peut pas modifier une
lecture effectuée plus tôt dans ce composant.

Dans Next.js, React Context est côté client. Placer le provider dans un Client
Component rendu depuis un layout serveur et transmettre des valeurs sérialisables.

Ne pas transformer Context en service locator caché. Exposer un hook ciblé qui
valide la présence du provider et fournit une API typée.

Références officielles :
[useContext](https://react.dev/reference/react/useContext) and
[Context providers in Next.js](https://nextjs.org/docs/app/getting-started/server-and-client-components#context-providers).
