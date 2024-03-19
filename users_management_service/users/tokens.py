from django.contrib.auth.tokens import PasswordResetTokenGenerator

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Ensure that the token is invalidated if the user's email is confirmed
        return (
            str(user.pk) + str(timestamp) +
            str(user.profile.email_confirmed)
        )

account_activation_token = AccountActivationTokenGenerator()
