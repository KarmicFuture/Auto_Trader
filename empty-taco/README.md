# Empty Taco

Promotional site for the Tampa mobile hot dog cart: menu, who we are, and a booking ticket to send the cart to your place.

## Local

```bash
python3 -m http.server 8080 --directory empty-taco
```

Then open http://localhost:8080

The booking form opens a mail draft to `book@emptytaco.com` (or copies the request). Change that address in `script.js` when the inbox is real.
