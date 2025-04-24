<?php
//
//declare(strict_types=1);
//
//namespace App\Modules\Projects\Forms;
//
//use App\Modules\Projects\Service\ProjectsService;
//use App\Common\Factory\FormFactory;
//use Nette;
//use Nette\Application\UI\Form;
//use Nette\Utils\ArrayHash;
//
///**
// * SOMSettingsFormFactory class
// *
// * This class is responsible for creating and managing the SOM settings form.
// */
//final class SOMSettingsFormFactory
//{
//    use Nette\SmartObject;
//
//    /** @var FormFactory */
//    private $factory;
//
//    private $projectsService;
//
//    /**
//     * Constructor for SOMSettingsFormFactory class
//     *
//     * @param FormFactory $factory Form factory.
//     */
//    public function __construct(
//        FormFactory $factory,
//        ProjectsService $projectsService
//    ) {
//        $this->factory = $factory;
//        $this->projectsService = $projectsService;
//    }
//
//    /**
//     * Creates and configures the SOM settings form.
//     *
//     * @return Form The configured SOM settings form.
//     */
//    public function createForm(callable $onSuccess): Form
//    {
//        $form = $this->factory->create();
//        $form->addProtection('Platnost formuláře vypršela, obnovte stránku.');
//
//        $form->addHidden('project_id');
//
//        // Learning rate
//        $form->addSelect('learning_rate', 'Learning rate', [
//            '0.9' => '0.9',
//            '0.8' => '0.8',
//            '0.7' => '0.7',
//            '0.6' => '0.6',
//            '0.5' => '0.5',
//            '0.4' => '0.4',
//            '0.3' => '0.3'
//        ])->setRequired('Vyberte learning rate');
//
//        // Min learning rate
//        $form->addSelect('min_learning_rate', 'Minimální learning rate', [
//            '0.3' => '0.3',
//            '0.2' => '0.2',
//            '0.1' => '0.1',
//            '0.05' => '0.05'
//        ])->setRequired('Vyberte minimální learning rate');
//
//        // Radius
//        $form->addSelect('radius', 'Počáteční poloměr sousedství', [
//            '10.0' => '10.0',
//            '5.0' => '5.0',
//            '2.0' => '2.0'
//        ])->setRequired('Vyberte počáteční poloměr');
//
//        // Min radius
//        $form->addSelect('min_radius', 'Minimální poloměr', [
//            '1.0' => '1.0',
//            '0.5' => '0.5',
//            '0.2' => '0.2',
//            '0.1' => '0.1'
//        ])->setRequired('Vyberte minimální poloměr');
//
//        // Num batches
//        $form->addInteger('num_batches', 'Počet batchů')
//            ->setDefaultValue(10)
//            ->setRequired('Zadejte počet batchů');
//
//        // Min batch percent
//        $form->addSelect('min_batch_percent', 'Minimální procento dat v batchi', [
//            '1.0' => '1.0',
//            '0.5' => '0.5',
//            '0.2' => '0.2',
//            '0.1' => '0.1'
//        ])->setRequired('Vyberte minimální procento dat');
//
//        // Max batch percent
//        $form->addSelect('max_batch_percent', 'Maximální procento dat v batchi', [
//            '10.0' => '10.0',
//            '5.0' => '5.0',
//            '2.0' => '2.0'
//        ])->setRequired('Vyberte maximální procento dat');
//
//        // Learning rate decay type
//        $form->addSelect('lr_decay_type', 'Typ útlumu learning rate', [
//            'linear-drop' => 'Lineární pokles',
//            'exp-drop' => 'Exponenciální pokles'
//        ])->setRequired('Vyberte typ útlumu learning rate');
//
//        // Radius decay type
//        $form->addSelect('radius_decay_type', 'Typ útlumu radiusu', [
//            'linear-drop' => 'Lineární pokles',
//            'exp-drop' => 'Exponenciální pokles'
//        ])->setRequired('Vyberte typ útlumu radiusu');
//
//        // Batch growth type
//        $form->addSelect('batch_growth_type', 'Typ růstu počtu vzorků', [
//            'exp-growth' => 'Exponenciální růst',
//            'linear-growth' => 'Lineární růst'
//        ])->setRequired('Vyberte typ růstu počtu vzorků');
//
//        // Random seed
//        $form->addInteger('random_seed', 'Náhodné semínko')
//            ->setNullable();
//
//        // Growth parameter G
//        $form->addSelect('growth_g', 'Parametr G pro růstovou funkci', [
//            '5.0' => '5.0',
//            '10.0' => '10.0',
//            '15.0' => '15.0',
//            '25.0' => '25.0',
//            '50.0' => '50.0'
//        ])->setRequired('Vyberte parametr G');
//
//        // Map size
//        $form->addSelect('map_size', 'Velikost výstupní mapy', [
//            '10,10' => '10x10',
//            '20,20' => '20x20',
//            '30,30' => '30x30'
//        ])->setRequired('Vyberte velikost mapy');
//
//        // Epoch multiplier
//        $form->addSelect('epoch_multiplier', 'Násobitel epoch', [
//            '1.0' => '1.0',
//            '5.0' => '5.0',
//            '10.0' => '10.0'
//        ])->setRequired('Vyberte násobitel epoch');
//
//        // Min Q error
//        $form->addSelect('min_q_error', 'Minimální kvalita mapy', [
//            '' => 'Žádná',
//            '0.1' => '0.1',
//            '0.01' => '0.01'
//        ]);
//
//        // Map type
//        $form->addSelect('map_type', 'Typ mapy', [
//            'square' => 'Čtvercová',
//            'hex' => 'Hexagonální'
//        ])->setRequired('Vyberte typ mapy');
//
//        // Normalize weights flag
//        $form->addCheckbox('normalize_weights_flag', 'Normalizovat váhy');
//
//        // Max epochs without improvement
//        $form->addSelect('max_epochs_without_improvement', 'Maximální počet epoch bez zlepšení', [
//            '' => 'Žádné omezení',
//            '50' => '50',
//            '100' => '100'
//        ]);
//
//        $form->addSubmit('submit', 'Uložit nastavení SOM');
//
//        $form->onValidate[] = function (Form $form, ArrayHash $values): void {
//            // form validation
//        };
//
//        $form->onSuccess[] = function (Form $form, ArrayHash $values) use ($onSuccess): void {
//            $project_id = $this->projectsService->saveSOMSettings($values);
//            $onSuccess($project_id);
//        };
//
//        return $form;
//    }
//}