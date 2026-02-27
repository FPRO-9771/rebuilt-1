#!/bin/bash
#
# Robot sub-menu (test, simulate, deploy)
#

menu_robot() {
    while true; do
        show_menu "Robot" \
            "1|Run tests|python -m pytest tests/ -v" \
            "2|Run simulation|python -m robotpy sim" \
            "---|" \
            "3|Deploy to robot|python -m robotpy deploy" \
            "4|Deploy to robot (skip tests)|python -m robotpy deploy --skip-tests" \
            "---|" \
            "5|Download packages for robot|python -m robotpy installer download ..." \
            "6|Install packages on robot|python -m robotpy installer install ..." \
            "b|Back"

        case "$MENU_CHOICE" in
            1)
                run_in_venv "Running Tests" \
                    python -m pytest tests/ -v
                ;;
            2)
                run_in_venv "Running Simulation" \
                    python -m robotpy sim
                ;;
            3)
                run_in_venv "Deploying to Robot" \
                    python -m robotpy deploy
                ;;
            4)
                run_in_venv "Deploying to Robot (skip tests)" \
                    python -m robotpy deploy --skip-tests
                ;;
            5)
                cmd_download_robot_packages
                ;;
            6)
                cmd_install_robot_packages
                ;;
            b) return ;;
            *) ;;
        esac
    done
}

cmd_download_robot_packages() {
    run_in_venv "Downloading Robot Packages" bash -c "
        echo 'Downloading Python for RoboRIO...'
        python -m robotpy installer download-python
        echo ''
        echo 'Downloading project packages for RoboRIO...'
        python -m robotpy installer download -r requirements.txt
    "
}

cmd_install_robot_packages() {
    run_in_venv "Installing Packages on Robot" bash -c "
        echo 'Make sure you are connected to the robot (USB or network).'
        echo ''
        echo 'Installing packages on RoboRIO...'
        python -m robotpy installer install -r requirements.txt
    "
}
