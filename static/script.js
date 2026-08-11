// ==========================================
// SWEET SCOOP SHOP
// ==========================================

let cart = [];


// ==========================================
// ADD TO CART
// ==========================================

function addToCart(name, price) {

    const existingItem = cart.find(
        item => item.name === name
    );

    if (existingItem) {

        existingItem.quantity += 1;

    } else {

        cart.push({
            name: name,
            price: price,
            quantity: 1
        });

    }

    updateCart();

}


// ==========================================
// UPDATE CART
// ==========================================

function updateCart() {

    const cartItems =
        document.getElementById("cart-items");

    const cartTotal =
        document.getElementById("cart-total");


    if (!cartItems || !cartTotal) {
        return;
    }


    cartItems.innerHTML = "";


    if (cart.length === 0) {

        cartItems.innerHTML =
            "<p>Your cart is empty 🍦</p>";

        cartTotal.textContent = "0";

        return;
    }


    let total = 0;


    cart.forEach((item, index) => {

        const itemTotal =
            item.price * item.quantity;

        total += itemTotal;


        const div =
            document.createElement("div");


        div.innerHTML = `
            <p>
                <strong>${item.name}</strong>
                × ${item.quantity}
                — GH₵ ${itemTotal}

                <button onclick="removeFromCart(${index})">
                    Remove
                </button>
            </p>
        `;


        cartItems.appendChild(div);

    });


    cartTotal.textContent = total;

}


// ==========================================
// REMOVE FROM CART
// ==========================================

function removeFromCart(index) {

    cart.splice(index, 1);

    updateCart();

}


// ==========================================
// OPEN CHECKOUT
// ==========================================

function openCheckout() {

    const checkout =
        document.getElementById("checkout");

    if (!checkout) {
        return;
    }


    const checkoutTotal =
        document.getElementById("checkout-total");


    const cartTotal =
        document.getElementById("cart-total");


    checkoutTotal.textContent =
        cartTotal.textContent;


    checkout.scrollIntoView({
        behavior: "smooth"
    });

}


// ==========================================
// PREPARE ORDER
// ==========================================

function prepareOrder() {

    const itemsInput =
        document.getElementById("order-items");

    const totalInput =
        document.getElementById("order-total");


    if (!itemsInput || !totalInput) {
        return;
    }


    let itemsText = "";


    cart.forEach(item => {

        itemsText +=
            item.name +
            " x " +
            item.quantity +
            " — GH₵ " +
            (item.price * item.quantity) +
            "\n";

    });


    const total =
        cart.reduce(
            (sum, item) =>
                sum + (item.price * item.quantity),
            0
        );


    itemsInput.value = itemsText;

    totalInput.value = total;

}


// ==========================================
// INITIALIZE
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateCart();

    }
);