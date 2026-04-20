<template>
  <div :class="` flex-center q-mt-xl ${isMobile ? '' : 'flex q-pt-xl'}`">
    <q-card bordered class="q-pa-lg" style="min-width: 40%;">
      <q-card-section class="text-center">
          <h1 class="q-mt-none q-mb-sm">Register</h1>
          <p>Register a new user account</p>
      </q-card-section>
      <q-form @submit="submit()">
        <q-input
          class="q-mt-md q-mb-sm"
          outlined
          label="Username"
          :rules="[requiredRule]"
          v-model="username"
          aria-required="true"
        />
        <q-input
          class="q-mb-sm"
          outlined
          label="Email Address"
          :rules="[requiredRule, emailRule]"
          v-model="email"
          aria-required="true"
        />
        <q-input
          class="q-mb-sm"
          outlined
          label="Password"
          :type="showPassword ? 'text' : 'password'"
          :rules="[
            requiredRule,
            minLengthRule,
            uppercaseRule,
            lowercaseRule,
            digitRule,
            specialCharRule,
          ]"
          hint="At least 15 characters, including upper and lower case letters, a digit, and a special character."
          v-model="password"
          aria-required="true"
        >
          <template v-slot:append>
            <q-icon
              :name="showPassword ? 'visibility' : 'visibility_off'"
              class="cursor-pointer"
              @click="showPassword = !showPassword"
            />
          </template>
        </q-input>
        <q-list dense class="q-mb-sm text-caption">
          <q-item-label caption>Password must contain:</q-item-label>
          <q-item dense>
            <q-item-section>- At least 15 characters</q-item-section>
          </q-item>
          <q-item dense>
            <q-item-section>- An uppercase letter (A-Z)</q-item-section>
          </q-item>
          <q-item dense>
            <q-item-section>- A lowercase letter (a-z)</q-item-section>
          </q-item>
          <q-item dense>
            <q-item-section>- A digit (0-9)</q-item-section>
          </q-item>
          <q-item dense>
            <q-item-section>- A special character (e.g. !@#$%^&amp;*)</q-item-section>
          </q-item>
        </q-list>
        <q-input
          class="q-mb-md"
          outlined
          label="Confirm Password"
          :type="showPassword ? 'text' : 'password'"
          :rules="[requiredRule, matchRule]"
          v-model="confirmPassword"
          aria-required="true"
        >
          <template v-slot:append>
            <q-icon
              :name="showPassword ? 'visibility' : 'visibility_off'"
              class="cursor-pointer"
              @click="showPassword = !showPassword"
            />
          </template>
        </q-input>
        <q-btn
          color="primary"
          class="full-width q-mt-md"
          type="submit"
        >
          Register
        </q-btn>
        <q-card-section class="text-center q-pt-md">
          <p>Go back to
            <router-link 
              role="button" 
              class="text-weight-bold text-primary" 
              style="text-decoration: none; cursor: pointer" 
              to="/login"
            >
              Login Menu.
            </router-link >
          </p>
        </q-card-section>
      </q-form>
    </q-card>
  </div>
</template>

<script setup>
  import { ref, inject } from 'vue';
  import * as notify from '../notify';
  import * as api from '@/services/dataApi';
  import { useRouter } from 'vue-router'
  
  const router = useRouter()

  const isMobile = inject('isMobile')

  const requiredRule = (val) => (val && val.length > 0) || "This field is required";
  const matchRule = (val) => (val && val === password.value) || 'Password mismatch';
  const emailRule = val => {
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    return (val && emailRegex.test(val)) || "Invalid email address";
  };
  const minLengthRule = (val) =>
    (val && val.length >= 15) || "Password must be at least 15 characters long";
  const uppercaseRule = (val) =>
    /[A-Z]/.test(val || "") || "Password must contain an uppercase letter";
  const lowercaseRule = (val) =>
    /[a-z]/.test(val || "") || "Password must contain a lowercase letter";
  const digitRule = (val) =>
    /\d/.test(val || "") || "Password must contain a digit";
  const specialCharRule = (val) =>
    /[!-/:-@\[-`{-~]/.test(val || "") ||
    "Password must contain a special character";

  const username = ref('');
  const password = ref('');
  const email = ref('');
  const confirmPassword = ref('');
  const showPassword = ref(false);

  async function submit() {
    try {
      const res = await api.registerUser(username.value, email.value, password.value, confirmPassword.value);
      router.push('/login')
      notify.success(`Successfully created user '${res.data.username}'`);
    } catch (err) {
      notify.error(err.response.data.message);
    }
  }

</script>