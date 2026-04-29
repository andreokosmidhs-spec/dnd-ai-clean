// Read an uploaded image File and resize it client-side so the resulting
// data URL stays under ~600 KB (well within JSON body limits and small
// enough that we never pay portrait-prompt round-trip for a 5MB phone photo).
//
// Returns a JPEG data URL on success, or rejects with an Error.

const MAX_SIDE_PX = 1024;
const QUALITY = 0.85;

export const fileToCompressedDataUrl = (file) =>
  new Promise((resolve, reject) => {
    if (!file) return reject(new Error("No file selected"));
    if (!file.type.startsWith("image/")) {
      return reject(new Error("Please choose an image file (PNG, JPG, WEBP)."));
    }
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.onload = () => {
      const img = new Image();
      img.onerror = () => reject(new Error("Could not decode the image"));
      img.onload = () => {
        const { width, height } = img;
        const longest = Math.max(width, height);
        const scale = longest > MAX_SIDE_PX ? MAX_SIDE_PX / longest : 1;
        const w = Math.round(width * scale);
        const h = Math.round(height * scale);

        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (!ctx) return reject(new Error("Canvas not supported"));
        ctx.drawImage(img, 0, 0, w, h);
        try {
          const dataUrl = canvas.toDataURL("image/jpeg", QUALITY);
          resolve(dataUrl);
        } catch (e) {
          reject(e);
        }
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  });
