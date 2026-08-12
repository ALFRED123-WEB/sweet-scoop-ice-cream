// ==========================================
// SWEET SCOOP SHOP - CART SYSTEM
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
// INCREASE QUANTITY
// ==========================================

function increaseQuantity(index) {

    if (!cart[index]) {
        return;
    }

    cart[index].quantity += 1;

    updateCart();
}


// ==========================================
// DECREASE QUANTITY
// ==========================================

function decreaseQuantity(index) {

    if (!cart[index]) {
        return;
    }

    if (cart[index].quantity > 1) {

        cart[index].quantity -= 1;

    } else {

        cart.splice(index, 1);

    }

    updateCart();
}


// ==========================================
// REMOVE FROM CART
// ==========================================

function removeFromCart(index) {

    if (!cart[index]) {
        return;
    }

    cart.splice(index, 1);

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

    const cartCount =
        document.getElementById("cart-count");

    const checkoutTotal =
        document.getElementById("checkout-total");


    // ======================================
    // UPDATE CART COUNTER
    // ======================================

    if (cartCount) {

        const totalQuantity = cart.reduce(
            (sum, item) => sum + item.quantity,
            0
        );

        cartCount.textContent = totalQuantity;
    }


    // ======================================
    // CHECK CART ELEMENTS
    // ======================================

    if (!cartItems || !cartTotal) {
        return;
    }


    // Clear current cart display

    cartItems.innerHTML = "";


    // ======================================
    // EMPTY CART
    // ======================================

    if (cart.length === 0) {

        cartItems.innerHTML =
            "<p>Your cart is empty 🍦</p>";

        cartTotal.textContent = "0";


        if (checkoutTotal) {

            checkoutTotal.textContent = "0";

        }

        return;
    }


    // ======================================
    // CALCULATE TOTAL
    // ======================================

    let total = 0;


    // ======================================
    // DISPLAY CART ITEMS
    // ======================================

    cart.forEach((item, index) => {

        const itemTotal =
            item.price * item.quantity;

        total += itemTotal;


        const div =
            document.createElement("div");

        div.className = "cart-item";


        div.innerHTML = `

            <div class="cart-item-info">

                <strong>
                    ${item.name}
                </strong>

                <span>
                    GH₵ ${item.price} each
                </span>

            </div>


            <div class="cart-item-controls">

                <button
                    type="button"
                    onclick="decreaseQuantity(${index})"
                >
                    −
                </button>


                <span class="quantity">
                    ${item.quantity}
                </span>


                <button
                    type="button"
                    onclick="increaseQuantity(${index})"
                >
                    +
                </button>

            </div>


            <div class="cart-item-total">

                GH₵ ${itemTotal}

            </div>


            <button
                type="button"
                class="remove-button"
                onclick="removeFromCart(${index})"
            >
                Remove
            </button>

        `;


        cartItems.appendChild(div);

    });


    // ======================================
    // UPDATE TOTAL
    // ======================================

    cartTotal.textContent = total;


    if (checkoutTotal) {

        checkoutTotal.textContent = total;

    }
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


    if (checkoutTotal && cartTotal) {

        checkoutTotal.textContent =
            cartTotal.textContent;

    }


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

        return false;
    }


    // ======================================
    // DON'T ALLOW EMPTY ORDERS
    // ======================================

    if (cart.length === 0) {

        alert(
            "Your cart is empty. Please add an ice cream first 🍦"
        );

        return false;
    }


    // ======================================
    // PREPARE ITEMS
    // ======================================

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


    // ======================================
    // CALCULATE TOTAL
    // ======================================

    const total =
        cart.reduce(
            (sum, item) =>
                sum +
                (item.price * item.quantity),
            0
        );


    // ======================================
    // SEND DATA TO FLASK
    // ======================================

    itemsInput.value = itemsText;

    totalInput.value = total;


    return true;
}


// ==========================================
// INITIALIZE CART
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updateCart();

    }
);